import calendar
from datetime import date, datetime, timedelta

from django.db import transaction
from django.db.models import Count
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import Section
from communication.services import notify
from core.audit import client_ip
from core.roles import ACADEMIC, HR, R, STUDENT_VIEWERS, has_role, is_admin
from core.scopes import by_student, teacher_section_ids, visible_student_ids
from core.viewsets import BaseModelViewSet
from people.models import Employee, Student

from . import serializers as s
from .models import Source, StaffAttendance, Status, StudentAttendance
from .services import attendance_percentage, is_holiday

G = "Attendance"


class StudentAttendanceViewSet(BaseModelViewSet):
    queryset = StudentAttendance.objects.all()
    serializer_class = s.StudentAttendanceSerializer
    resource_key = "student-attendance"
    read_roles = STUDENT_VIEWERS
    write_roles = ACADEMIC + [R.TEACHER, R.HOSTEL_WARDEN]
    scope = by_student()
    search_fields = ["student__admission_no", "student__user__first_name"]
    filterset_fields = ["date", "student", "section", "subject", "status", "source"]
    label, group, icon, menu = "Student Attendance", G, "check", False
    list_fields = ["date", "student", "section", "subject", "status", "source", "marked_by"]


class StaffAttendanceViewSet(BaseModelViewSet):
    queryset = StaffAttendance.objects.all()
    serializer_class = s.StaffAttendanceSerializer
    resource_key = "staff-attendance"
    read_roles = HR + ACADEMIC
    write_roles = HR
    scope = staticmethod(lambda qs, user: qs.filter(employee__user=user))
    search_fields = ["employee__employee_no", "employee__user__first_name"]
    filterset_fields = ["date", "employee", "status", "source"]
    label, group, icon, menu = "Staff Attendance", G, "check-circle", False
    list_fields = ["date", "employee", "status", "check_in", "check_out", "source"]


def _date(value, default=None):
    if not value:
        return default or timezone.localdate()
    return datetime.strptime(value, "%Y-%m-%d").date() if isinstance(value, str) else value


def can_mark_section(user, section_id):
    return is_admin(user) or has_role(user, ACADEMIC + [R.HOSTEL_WARDEN]) or int(section_id) in teacher_section_ids(user)


class AttendanceSheetView(APIView):
    """GET roster for a section/date/subject with existing statuses."""

    def get(self, request):
        section_id = request.query_params.get("section")
        if not section_id:
            raise ValidationError({"section": "Required"})
        if not can_mark_section(request.user, section_id):
            raise PermissionDenied("You are not assigned to this section.")
        d = _date(request.query_params.get("date"))
        subject = request.query_params.get("subject") or None
        existing = {a.student_id: a for a in StudentAttendance.objects.filter(section_id=section_id, date=d, subject_id=subject)}
        from leaves.models import LeaveRequest
        on_leave = set(LeaveRequest.objects.filter(status="approved", start_date__lte=d, end_date__gte=d)
                       .values_list("user_id", flat=True))
        rows = []
        for st in Student.objects.filter(section_id=section_id, status="active").select_related("user"):
            a = existing.get(st.id)
            rows.append({"student": st.id, "name": st.user.display_name, "admission_no": st.admission_no, "roll_no": st.roll_no,
                         "status": a.status if a else ("leave" if st.user_id in on_leave else None),
                         "remarks": a.remarks if a else "", "on_leave": st.user_id in on_leave})
        return Response({"date": d, "section": section_id, "subject": subject, "is_holiday": is_holiday(d),
                         "already_marked": bool(existing), "students": rows})


class BulkMarkView(APIView):
    """POST {section, date, subject?, time_slot?, records:[{student, status, remarks}]}"""

    @transaction.atomic
    def post(self, request):
        ser = s.BulkMarkSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        if not can_mark_section(request.user, d["section"]):
            raise PermissionDenied("You are not assigned to this section.")
        if d["date"] > timezone.localdate():
            raise ValidationError({"date": "Cannot mark attendance for a future date."})
        valid = set(Student.objects.filter(section_id=d["section"]).values_list("id", flat=True))
        from website.models import SiteSettings
        notify_guardian = SiteSettings.get().notify_guardian_on_absence and not d.get("subject")
        count = 0
        for rec in d["records"]:
            if rec["student"] not in valid:
                continue
            obj, _ = StudentAttendance.objects.update_or_create(
                student_id=rec["student"], date=d["date"], subject_id=d.get("subject"),
                defaults={"section_id": d["section"], "status": rec["status"], "remarks": rec["remarks"],
                          "time_slot_id": d.get("time_slot"), "marked_by": request.user, "source": Source.MANUAL})
            count += 1
            if notify_guardian and rec["status"] == Status.ABSENT and not obj.guardian_notified:
                st = obj.student
                users = [g.user for g in (st.guardian, st.second_guardian) if g and g.user_id]
                if users:
                    notify(users, f"{st.user.display_name} was absent on {d['date']:%d %b %Y}",
                           "Please contact the madrasa if this is unexpected.", "/attendance", "attendance")
                    obj.guardian_notified = True
                    obj.save(update_fields=["guardian_notified"])
        return Response({"detail": f"Attendance saved for {count} student(s).", "count": count})


class StaffSelfView(APIView):
    """Staff self check-in / check-out (records IP and optional GPS)."""

    def _employee(self, user):
        emp = getattr(user, "employee_profile", None)
        if not emp:
            raise ValidationError({"detail": "No employee profile linked to your account."})
        return emp

    def _payload(self, emp):
        rec = StaffAttendance.objects.filter(employee=emp, date=timezone.localdate()).first()
        history = StaffAttendance.objects.filter(employee=emp).order_by("-date")[:31]
        return Response({
            "today": {"status": rec.status if rec else None, "check_in": rec.check_in if rec else None,
                      "check_out": rec.check_out if rec else None, "hours": rec.hours_worked if rec else None},
            "history": [{"date": h.date, "status": h.get_status_display(), "check_in": h.check_in,
                         "check_out": h.check_out, "hours": h.hours_worked} for h in history],
        })

    def get(self, request):
        return self._payload(self._employee(request.user))

    def post(self, request):
        emp = self._employee(request.user)
        ser = s.SelfCheckSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        today = timezone.localdate()
        now = timezone.localtime().time().replace(microsecond=0)
        rec = StaffAttendance.objects.filter(employee=emp, date=today).first()
        if ser.validated_data["action"] == "check_in":
            if rec and rec.check_in:
                raise ValidationError({"detail": "Already checked in today."})
            status = Status.PRESENT
            if emp.duty_start:
                from website.models import SiteSettings
                grace = SiteSettings.get().attendance_late_after_minutes
                if now > (datetime.combine(today, emp.duty_start) + timedelta(minutes=grace)).time():
                    status = Status.LATE
            StaffAttendance.objects.update_or_create(
                employee=emp, date=today,
                defaults={"check_in": now, "status": status, "source": Source.SELF, "ip_address": client_ip(request),
                          "check_in_location": ser.validated_data["location"]})
        else:
            if not rec or not rec.check_in:
                raise ValidationError({"detail": "You have not checked in today."})
            rec.check_out = now
            rec.save(update_fields=["check_out", "updated_at"])
        return self._payload(emp)


class StaffSheetView(APIView):
    def get(self, request):
        if not has_role(request.user, HR + ACADEMIC):
            raise PermissionDenied()
        d = _date(request.query_params.get("date"))
        existing = {a.employee_id: a for a in StaffAttendance.objects.filter(date=d)}
        rows = []
        for e in Employee.objects.filter(status="active").select_related("user"):
            a = existing.get(e.id)
            rows.append({"employee": e.id, "name": e.user.display_name, "designation": e.designation,
                         "employee_no": e.employee_no, "status": a.status if a else None,
                         "check_in": a.check_in if a else None, "check_out": a.check_out if a else None,
                         "remarks": a.remarks if a else ""})
        return Response({"date": d, "is_holiday": is_holiday(d), "staff": rows})


class StaffBulkView(APIView):
    @transaction.atomic
    def post(self, request):
        if not has_role(request.user, HR + ACADEMIC):
            raise PermissionDenied()
        ser = s.StaffBulkSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        for rec in d["records"]:
            StaffAttendance.objects.update_or_create(
                employee_id=rec["employee"], date=d["date"],
                defaults={"status": rec["status"], "check_in": rec.get("check_in"), "check_out": rec.get("check_out"),
                          "remarks": rec["remarks"], "marked_by": request.user, "source": Source.MANUAL})
        return Response({"detail": f"Saved {len(d['records'])} record(s).", "count": len(d["records"])})


class AttendanceReportView(APIView):
    """Per-student summary for ?section=&from=&to= (or ?student=)."""

    def get(self, request):
        user = request.user
        d_from = _date(request.query_params.get("from"), timezone.localdate().replace(day=1))
        d_to = _date(request.query_params.get("to"))
        qs = StudentAttendance.objects.filter(date__range=(d_from, d_to), subject__isnull=True)
        if request.query_params.get("section"):
            qs = qs.filter(section_id=request.query_params["section"])
        if request.query_params.get("student"):
            qs = qs.filter(student_id=request.query_params["student"])
        if not has_role(user, STUDENT_VIEWERS):
            qs = qs.filter(student_id__in=visible_student_ids(user))
        rows = {}
        for sid, status, c in qs.values_list("student_id", "status").annotate(c=Count("id")):
            rows.setdefault(sid, {})[status] = c
        from website.models import SiteSettings
        threshold = SiteSettings.get().min_attendance_percent
        students = {x.id: x for x in Student.objects.filter(id__in=rows.keys()).select_related("user", "section")}
        out = []
        for sid, summary in rows.items():
            st = students.get(sid)
            pct = attendance_percentage(summary)
            out.append({"student": sid, "name": st.user.display_name if st else sid, "admission_no": st.admission_no if st else "",
                        "section": str(st.section) if st and st.section else "", "summary": summary,
                        "total": sum(summary.values()), "percentage": pct,
                        "below_threshold": pct is not None and pct < threshold})
        out.sort(key=lambda r: (r["percentage"] is None, r["percentage"] or 0))
        return Response({"from": d_from, "to": d_to, "threshold": threshold, "rows": out})


class MonthlyRegisterView(APIView):
    """Register grid: ?section=&month=YYYY-MM -> students x days."""

    CODES = {"present": "P", "absent": "A", "late": "L", "leave": "Lv", "half_day": "H", "excused": "E", "holiday": "-"}

    def get(self, request):
        section = request.query_params.get("section")
        if not section or not (has_role(request.user, STUDENT_VIEWERS) or int(section) in teacher_section_ids(request.user)):
            raise PermissionDenied()
        month = request.query_params.get("month") or timezone.localdate().strftime("%Y-%m")
        y, m = map(int, month.split("-"))
        days = calendar.monthrange(y, m)[1]
        marks = {}
        for a in StudentAttendance.objects.filter(section_id=section, date__range=(date(y, m, 1), date(y, m, days)),
                                                  subject__isnull=True):
            marks.setdefault(a.student_id, {})[a.date.day] = a.status
        rows = []
        for st in Student.objects.filter(section_id=section, status="active").select_related("user"):
            row = marks.get(st.id, {})
            summary = {}
            for v in row.values():
                summary[v] = summary.get(v, 0) + 1
            rows.append({"student": st.id, "name": st.user.display_name, "admission_no": st.admission_no,
                         "days": [self.CODES.get(row.get(d), "") for d in range(1, days + 1)],
                         "percentage": attendance_percentage(summary)})
        holidays = [d for d in range(1, days + 1) if is_holiday(date(y, m, d))]
        return Response({"month": month, "days": days, "holidays": holidays, "rows": rows})


class MyAttendanceView(APIView):
    """Student / parent view."""

    def get(self, request):
        user = request.user
        allowed = None if has_role(user, STUDENT_VIEWERS) else visible_student_ids(user)
        sid = request.query_params.get("student")
        if not sid:
            if not allowed:
                return Response({"records": [], "summary": {}, "percentage": None})
            sid = sorted(allowed)[0]
        sid = int(sid)
        if allowed is not None and sid not in allowed:
            raise PermissionDenied()
        qs = StudentAttendance.objects.filter(student_id=sid, subject__isnull=True).order_by("-date")
        summary = dict(qs.values_list("status").annotate(c=Count("id")))
        return Response({"student": sid, "summary": summary, "percentage": attendance_percentage(summary),
                         "records": [{"date": a.date, "status": a.status, "status_display": a.get_status_display(),
                                      "remarks": a.remarks} for a in qs[:120]]})


class TodayOverviewView(APIView):
    def get(self, request):
        if not has_role(request.user, STUDENT_VIEWERS):
            raise PermissionDenied()
        d = _date(request.query_params.get("date"))
        sections = []
        for sec in Section.objects.filter(academic_year__is_current=True).select_related("class_level", "class_teacher"):
            agg = dict(StudentAttendance.objects.filter(section=sec, date=d, subject__isnull=True)
                       .values_list("status").annotate(c=Count("id")))
            sections.append({"section": sec.id, "label": str(sec),
                             "teacher": sec.class_teacher.display_name if sec.class_teacher else "",
                             "strength": sec.students.filter(status="active").count(), "summary": agg, "marked": bool(agg)})
        staff = dict(StaffAttendance.objects.filter(date=d).values_list("status").annotate(c=Count("id")))
        return Response({"date": d, "sections": sections, "staff": staff,
                         "staff_total": Employee.objects.filter(status="active").count()})


# ===================================================================== biometrics
from rest_framework.decorators import action  # noqa: E402
from rest_framework.parsers import FormParser, MultiPartParser  # noqa: E402
from rest_framework.permissions import AllowAny  # noqa: E402

from . import biometric  # noqa: E402
from .models import BiometricDevice, BiometricEnrollment, BiometricPunch  # noqa: E402

BIO = HR + ACADEMIC


class BiometricDeviceViewSet(BaseModelViewSet):
    queryset = BiometricDevice.objects.all()
    serializer_class = s.BiometricDeviceSerializer
    resource_key = "biometric-devices"
    read_roles = write_roles = BIO
    label, group, icon, menu = "Biometric Devices", G, "id", False
    list_fields = ["name", "serial_number", "protocol", "audience", "location", "is_active", "last_seen"]
    ui_actions = [{"name": "pull_now", "label": "Pull logs now (LAN)", "roles": BIO, "confirm": "Connect to the device and download new punches?"},
                  {"name": "regenerate_key", "label": "New API key", "roles": BIO, "confirm": "The old key will stop working. Continue?"}]

    @action(detail=True, methods=["post"])
    def pull_now(self, request, pk=None):
        try:
            r = biometric.pull_device(self.get_object())
        except biometric.BiometricError as e:
            return Response({"detail": str(e)}, status=400)
        return Response({"detail": f"{r['new']} new punch(es), {r['applied']} applied, {r['unmatched']} unknown PIN(s).", **r})

    @action(detail=True, methods=["post"])
    def regenerate_key(self, request, pk=None):
        d = self.get_object()
        d.api_key = BiometricDevice._meta.get_field("api_key").default()
        d.save(update_fields=["api_key"])
        return Response({"detail": "New API key generated.", "api_key": d.api_key})


class BiometricEnrollmentViewSet(BaseModelViewSet):
    queryset = BiometricEnrollment.objects.all()
    serializer_class = s.BiometricEnrollmentSerializer
    resource_key = "biometric-enrollments"
    read_roles = write_roles = BIO
    search_fields = ["pin", "card_number", "user__first_name", "user__last_name", "user__username"]
    filterset_fields = ["is_active", "fingerprint", "face", "user__role"]
    label, group, icon, menu = "Biometric Enrolments", G, "users", False
    list_fields = ["pin", "user", "card_number", "fingerprint", "face", "is_active"]

    def after_save(self, obj, created):
        # punches that arrived before this PIN was linked to a person
        for p in BiometricPunch.objects.filter(pin=obj.pin).exclude(result=BiometricPunch.Result.APPLIED).order_by("punched_at"):
            biometric.process_punch(p)


class BiometricPunchViewSet(BaseModelViewSet):
    queryset = BiometricPunch.objects.all()
    serializer_class = s.BiometricPunchSerializer
    resource_key = "biometric-punches"
    read_roles = BIO
    read_only = True
    scope = staticmethod(lambda qs, user: qs.filter(user=user))  # everyone can see their own punches
    search_fields = ["pin", "user__first_name", "user__last_name"]
    filterset_fields = ["device", "result", "direction", "user", "pin", "source"]
    label, group, icon, menu = "Biometric Punch Log", G, "list", False
    list_fields = ["punched_at", "pin", "user", "device", "direction", "verify_mode", "result"]


class BioAPIView(APIView):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not has_role(request.user, BIO):
            raise PermissionDenied()


class BiometricStatusView(BioAPIView):
    def get(self, request):
        data = biometric.status_summary()
        host = request.get_host()
        data["push_server"] = {"address": host.split(":")[0], "port": host.split(":")[1] if ":" in host else ("443" if request.is_secure() else "80"),
                               "url": f"{request.scheme}://{host}/iclock/cdata"}
        data["api_url"] = request.build_absolute_uri("/api/biometric/punches/")
        try:
            import zk  # noqa: F401
            data["pull_available"] = True
        except ImportError:
            data["pull_available"] = False
        return Response(data)


class BiometricImportView(BioAPIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        ser = s.BiometricImportSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            rows, errors = biometric.parse_csv(ser.validated_data["file"].read())
        except biometric.BiometricError as e:
            return Response({"detail": str(e)}, status=400)
        if not rows:
            return Response({"detail": "No punches found in the file.", "errors": errors[:20]}, status=400)
        r = biometric.record_punches(ser.validated_data.get("device"), rows, "csv")
        return Response({"detail": f"Imported {r['new']} new punch(es) ({r['duplicates']} duplicates): {r['applied']} applied, "
                                   f"{r['unmatched']} unknown PIN(s), {r['skipped']} skipped.", **r, "errors": errors[:20]})


class BiometricProcessView(BioAPIView):
    def post(self, request):
        ser = s.DateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        r = biometric.reprocess(ser.validated_data["date"], ser.validated_data["include_applied"])
        return Response({"detail": f"Processed: {r['applied']} applied, {r['unmatched']} unknown PIN(s), {r['skipped']} skipped.", **r})


class BiometricCloseDayView(BioAPIView):
    def post(self, request):
        ser = s.DateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        if d["date"] > timezone.localdate():
            raise ValidationError({"date": "Cannot close a future date."})
        r = biometric.close_day(d["date"], d["staff"], d["students"])
        return Response({"detail": r.get("detail") or f"Marked absent: {r['staff']} staff, {r['students']} student(s) without a punch.", **r})


class BiometricAutoEnrollView(BioAPIView):
    def post(self, request):
        ser = s.AutoEnrollSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        n = biometric.auto_enroll(**ser.validated_data)
        return Response({"detail": f"{n} PIN(s) created. Enrol the same IDs on the device (fingerprint / face / card)."})


class DevicePunchAPIView(APIView):
    """JSON API for other vendors' software: header `X-Device-Key: <device api key>`."""

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        key = request.headers.get("X-Device-Key") or request.data.get("device_key")
        device = BiometricDevice.objects.filter(api_key=key, is_active=True).first() if key else None
        if not device:
            return Response({"detail": "Invalid or missing device key."}, status=401)
        ser = s.PunchBatchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        try:
            rows = [{"pin": p["pin"].strip(), "time": biometric.parse_datetime(p["time"]), "direction": biometric._direction(p["direction"]),
                     "verify": p["verify"], "raw": f"{p['pin']} {p['time']}"} for p in ser.validated_data["punches"]]
        except biometric.BiometricError as e:
            return Response({"detail": str(e)}, status=400)
        return Response(biometric.record_punches(device, rows, "api"))
