import secrets

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from accounts.serializers import user_payload
from core.audit import audit
from core.roles import (ACADEMIC, ADMISSION, FRONT_DESK, HOSTEL, HR, R, Role, STAFF_ROLES, STUDENT_VIEWERS, has_role,
                        is_admin)
from core.scopes import by_student, by_user, children_qs, teacher_section_ids, visible_student_ids, visible_user_ids
from core.viewsets import BaseModelViewSet

from . import serializers as s
from .models import (Achievement, AdmissionApplication, AdmissionDocument, DisciplinaryRecord, Employee, EmploymentHistory, Guardian,
                     MedicalRecord, PersonDocument, Qualification, Student, StudentPromotion, VisitorLog)

G = "People & Records"
REC = "Personal Records"
GENDER = [{"value": "male", "label": "Male"}, {"value": "female", "label": "Female"}]


def user_form_fields(with_roles=None):
    """Virtual form fields for creating the login account with a profile."""
    f = [
        {"name": "first_name", "label": "First name", "type": "string", "required": True},
        {"name": "last_name", "label": "Last name", "type": "string", "required": False},
        {"name": "father_name", "label": "Father's name", "type": "string", "required": False},
        {"name": "gender", "label": "Gender", "type": "choice", "choices": GENDER, "required": False},
        {"name": "date_of_birth", "label": "Date of birth", "type": "date", "required": False},
        {"name": "cnic", "label": "CNIC / B-Form", "type": "string", "required": False},
        {"name": "phone", "label": "Phone", "type": "string", "required": False},
        {"name": "email", "label": "Email", "type": "email", "required": False},
        {"name": "address", "label": "Address", "type": "text", "required": False},
        {"name": "city", "label": "City", "type": "string", "required": False},
        {"name": "username", "label": "Login username", "type": "string", "required": False, "help": "Auto-generated if empty"},
        {"name": "password", "label": "Login password", "type": "string", "required": False,
         "help": "Leave empty to auto-generate (create) or keep unchanged (edit)"},
    ]
    if with_roles:
        f.insert(0, {"name": "role", "label": "Portal role", "type": "choice", "required": True,
                     "choices": [{"value": v, "label": l} for v, l in Role.choices if v in with_roles]})
    return f


def guardian_scope(qs, user):
    if user.role == R.PARENT:
        return qs.filter(user=user)
    return qs.filter(students__id__in=visible_student_ids(user)).distinct()


def employee_scope(qs, user):
    return qs.filter(user=user) if user.role in STAFF_ROLES else qs.none()


class StudentViewSet(BaseModelViewSet):
    queryset = Student.objects.all()
    serializer_class = s.StudentSerializer
    resource_key = "students"
    read_roles = STUDENT_VIEWERS
    write_roles = ADMISSION + [R.HR_MANAGER]
    scope = by_student("id")
    search_fields = ["admission_no", "roll_no", "user__first_name", "user__last_name", "user__father_name", "user__cnic"]
    filterset_fields = ["section", "department", "status", "is_boarder", "is_orphan", "is_zakat_eligible", "guardian"]
    group, icon = G, "student"
    list_fields = ["admission_no", "full_name", "father_name", "section", "department", "status", "phone"]
    extra_fields = user_form_fields()
    menu_roles = STUDENT_VIEWERS + [R.TEACHER, R.PARENT]
    ui_actions = [{"name": "set_status", "label": "Change status", "roles": ADMISSION,
                   "input": [{"name": "status", "type": "choice", "label": "New status",
                              "choices": [{"value": v, "label": l} for v, l in Student.Status.choices]},
                             {"name": "reason", "type": "string", "label": "Reason"}]}]

    @action(detail=True, methods=["post"])
    def set_status(self, request, pk=None):
        st = self.get_object()
        new = request.data.get("status")
        if new not in Student.Status.values:
            return Response({"detail": "Invalid status."}, status=400)
        previous = st.status
        st.status = new
        if new == "active" and previous in ("struck_off", "suspended"):
            st.leaving_date = None  # reinstated
            st.leaving_reason = f"Reinstated {timezone.localdate():%d %b %Y}: {request.data.get('reason', '')}".strip(": ")[:200]
        if new in ("left", "graduated", "transferred"):
            st.leaving_date = timezone.localdate()
            st.leaving_reason = request.data.get("reason", st.leaving_reason)
            st.user.is_active = new != "left"
            st.user.save(update_fields=["is_active"])
        st.save()
        audit(request, "set_status", st, "students", {"status": new})
        return Response({"detail": f"Status changed to {st.get_status_display()}."})


class EmployeeViewSet(BaseModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = s.EmployeeSerializer
    resource_key = "employees"
    read_roles = HR + ACADEMIC + [R.ACCOUNTANT]
    write_roles = HR
    scope = employee_scope
    search_fields = ["employee_no", "designation", "user__first_name", "user__last_name", "user__cnic"]
    filterset_fields = ["kind", "department", "status", "employment_type", "show_on_website"]
    label, group, icon = "Staff & Teachers", G, "briefcase"
    list_fields = ["employee_no", "full_name", "designation", "kind", "department", "status", "phone"]
    extra_fields = user_form_fields(with_roles=[r for r in Role.values if r not in (R.STUDENT, R.PARENT)])
    menu_roles = HR + ACADEMIC + [R.ACCOUNTANT]


class GuardianViewSet(BaseModelViewSet):
    queryset = Guardian.objects.all()
    serializer_class = s.GuardianSerializer
    resource_key = "guardians"
    read_roles = STUDENT_VIEWERS
    write_roles = ADMISSION + FRONT_DESK
    scope = guardian_scope
    search_fields = ["name", "phone", "cnic"]
    label, group, icon = "Parents / Guardians", G, "family"
    list_fields = ["name", "relation", "phone", "cnic", "occupation", "user"]
    extra_fields = [
        {"name": "create_login", "label": "Create parent portal login", "type": "boolean", "required": False},
        {"name": "login_username", "label": "Parent username", "type": "string", "required": False},
        {"name": "login_password", "label": "Parent password", "type": "string", "required": False},
    ]


class AdmissionApplicationViewSet(BaseModelViewSet):
    queryset = AdmissionApplication.objects.all()
    serializer_class = s.AdmissionApplicationSerializer
    resource_key = "admissions"
    read_roles = ADMISSION + [R.RECEPTIONIST]
    write_roles = ADMISSION
    search_fields = ["application_no", "full_name", "father_name", "phone", "guardian_phone"]
    filterset_fields = ["status", "source", "program", "session", "department", "class_level", "gender", "needs_hostel",
                        "requests_scholarship"]
    label, group, icon = "Admission Applications", "Admissions", "inbox"
    list_fields = ["application_no", "full_name", "father_name", "program", "department", "aggregate", "source", "status", "created_at"]
    ui_actions = [{"name": "enroll", "label": "Enroll student", "roles": ADMISSION,
                   "confirm": "Create a student account from this application?",
                   "input": [{"name": "section", "type": "fk", "resource": "sections", "label": "Assign section"}]}]

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def enroll(self, request, pk=None):
        app = self.get_object()
        if app.status == AdmissionApplication.Status.ENROLLED:
            return Response({"detail": "Already enrolled."}, status=400)
        first, _, last = app.full_name.partition(" ")
        username = f"std{timezone.now():%y}{secrets.token_hex(2)}"
        password = secrets.token_urlsafe(6)
        user = User(username=username, role=R.STUDENT, first_name=first, last_name=last, father_name=app.father_name,
                    gender=app.gender, date_of_birth=app.date_of_birth, cnic=app.cnic, phone=app.phone, email=app.email,
                    address=app.address, city=app.city, must_change_password=True)
        if app.photo:
            user.photo = app.photo
        user.set_password(password)
        user.save()
        relation = app.guardian_relation if app.guardian_relation in Guardian.Relation.values else "other"
        guardian = Guardian.objects.filter(phone=app.guardian_phone).first() or Guardian.objects.create(
            name=app.guardian_name, relation=relation, phone=app.guardian_phone, cnic=app.guardian_cnic,
            occupation=app.guardian_occupation, address=app.address, email=app.email)
        n = Student.objects.count() + 1
        adm_no = f"{timezone.now():%Y}-{n:04d}"
        while Student.objects.filter(admission_no=adm_no).exists():
            n += 1
            adm_no = f"{timezone.now():%Y}-{n:04d}"
        student = Student.objects.create(
            user=user, admission_no=adm_no, department=app.department, section_id=request.data.get("section") or None,
            guardian=guardian, previous_institution=app.previous_institution, previous_education=app.previous_education,
            is_boarder=app.needs_hostel, is_zakat_eligible=app.requests_scholarship)
        if app.document:
            PersonDocument.objects.create(person=user, title="Admission document", file=app.document, uploaded_by=request.user)
        for d in app.documents.all():
            PersonDocument.objects.create(person=user, title=f"Admission — {d.get_kind_display()}", file=d.file, uploaded_by=request.user)
        app.status = AdmissionApplication.Status.ENROLLED
        app.enrolled_student = student
        app.save()
        audit(request, "enroll", app, "admissions", {"student": adm_no})
        return Response({"detail": f"Enrolled as {adm_no}.", "student_id": student.id, "admission_no": adm_no,
                         "username": username, "password": password})


class AdmissionDocumentViewSet(BaseModelViewSet):
    """Files attached to online applications (private — staff only)."""
    queryset = AdmissionDocument.objects.all()
    serializer_class = s.AdmissionDocumentSerializer
    resource_key = "admission-documents"
    read_roles = ADMISSION + [R.RECEPTIONIST]
    write_roles = ADMISSION
    filterset_fields = ["application", "kind"]
    search_fields = ["application__application_no", "application__full_name"]
    label, group, icon = "Application documents", "Admissions", "folder"
    list_fields = ["application", "kind", "original_name", "file", "created_at"]


class StudentPromotionViewSet(BaseModelViewSet):
    queryset = StudentPromotion.objects.all()
    serializer_class = s.StudentPromotionSerializer
    resource_key = "promotions"
    read_roles = STUDENT_VIEWERS
    write_roles = ACADEMIC + [R.EXAM_CONTROLLER]
    scope = by_student()
    label, group, icon = "Promotion History", "Admissions", "trending"
    list_fields = ["student", "from_section", "to_section", "result", "date"]


class QualificationViewSet(BaseModelViewSet):
    queryset = Qualification.objects.all()
    serializer_class = s.QualificationSerializer
    resource_key = "qualifications"
    read_roles = HR + ACADEMIC
    write_roles = HR + ADMISSION
    scope = by_user("person")
    search_fields = ["title", "institution"]
    group, icon = REC, "award"
    list_fields = ["person", "title", "institution", "year", "grade"]


class EmploymentHistoryViewSet(BaseModelViewSet):
    queryset = EmploymentHistory.objects.all()
    serializer_class = s.EmploymentHistorySerializer
    resource_key = "employment-history"
    read_roles = HR
    write_roles = HR
    label, group, icon = "Employment History", REC, "history"
    list_fields = ["employee", "organization", "position", "from_date", "to_date"]


class PersonDocumentViewSet(BaseModelViewSet):
    queryset = PersonDocument.objects.all()
    serializer_class = s.PersonDocumentSerializer
    resource_key = "documents"
    read_roles = HR + ADMISSION
    write_roles = HR + ADMISSION
    scope = by_user("person")
    search_fields = ["title", "person__first_name"]
    label, group, icon = "Documents", REC, "file"
    list_fields = ["person", "title", "kind", "expiry_date", "created_at"]


class DisciplinaryRecordViewSet(BaseModelViewSet):
    queryset = DisciplinaryRecord.objects.all()
    serializer_class = s.DisciplinaryRecordSerializer
    resource_key = "disciplinary"
    read_roles = ACADEMIC + HR + HOSTEL
    write_roles = ACADEMIC + HR + HOSTEL + [R.TEACHER]
    scope = by_user("person")
    label, group, icon = "Disciplinary Records", REC, "alert"
    list_fields = ["person", "date", "severity", "incident", "guardian_informed"]


class MedicalRecordViewSet(BaseModelViewSet):
    queryset = MedicalRecord.objects.all()
    serializer_class = s.MedicalRecordSerializer
    resource_key = "medical"
    read_roles = ACADEMIC + HR + HOSTEL
    write_roles = ACADEMIC + HR + HOSTEL
    scope = by_user("person")
    label, group, icon = "Medical Records", REC, "heart"
    list_fields = ["person", "date", "condition", "doctor", "follow_up"]


class AchievementViewSet(BaseModelViewSet):
    queryset = Achievement.objects.all()
    serializer_class = s.AchievementSerializer
    resource_key = "achievements"
    read_roles = STUDENT_VIEWERS
    write_roles = ACADEMIC + [R.TEACHER]
    scope = by_user("person")
    group, icon = REC, "star"
    list_fields = ["person", "title", "category", "date"]


class VisitorLogViewSet(BaseModelViewSet):
    queryset = VisitorLog.objects.all()
    serializer_class = s.VisitorLogSerializer
    resource_key = "visitors"
    read_roles = FRONT_DESK + HOSTEL
    write_roles = FRONT_DESK + HOSTEL
    search_fields = ["name", "phone", "cnic", "purpose"]
    label, group, icon = "Visitor Log", "Front Desk", "door"
    list_fields = ["name", "phone", "purpose", "person_to_meet", "check_in", "check_out"]


# ------------------------------------------------------------------ APIViews
class PromoteView(APIView):
    """Bulk promote / detain / graduate students."""

    @transaction.atomic
    def post(self, request):
        if not has_role(request.user, ACADEMIC + [R.EXAM_CONTROLLER]):
            raise PermissionDenied()
        ser = s.PromoteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        done = 0
        for st in Student.objects.filter(id__in=d["student_ids"]):
            StudentPromotion.objects.create(student=st, from_section_id=st.section_id, to_section_id=d.get("to_section"),
                                            result=d["result"], remarks=d["remarks"], recorded_by=request.user)
            if d["result"] == "graduated":
                st.status = Student.Status.GRADUATED
                st.leaving_date = timezone.localdate()
            elif d["result"] == "promoted" and d.get("to_section"):
                st.section_id = d["to_section"]
            st.save()
            done += 1
        return Response({"detail": f"{done} student(s) processed."})


def can_view_person(viewer, target):
    if is_admin(viewer) or viewer.id == target.id:
        return True
    if target.role == R.STUDENT and has_role(viewer, STUDENT_VIEWERS):
        return True
    if target.role not in (R.STUDENT, R.PARENT) and has_role(viewer, HR + ACADEMIC):
        return True
    return target.id in visible_user_ids(viewer)


def _rows(qs, fields):
    out = []
    for o in qs:
        row = {}
        for f in fields:
            v = o
            for part in f.split("."):
                v = getattr(v, part, None) if v is not None else None
            if hasattr(v, "isoformat"):
                v = v.isoformat()
            elif v is not None and not isinstance(v, (int, float, bool, str)):
                v = str(v)
            row[f.replace(".", "_")] = v
        out.append(row)
    return out


class Profile360View(APIView):
    """Everything the institution knows about one person, in one response."""

    def get(self, request, user_id):
        from attendance.models import StaffAttendance, StudentAttendance
        from exams.models import Certificate, Mark
        from finance.models import Invoice, Payslip
        from hifz.models import JuzProgress
        from hostel.models import HostelAllocation
        from leaves.models import LeaveRequest
        from library.models import BookIssue
        from transport.models import TransportAssignment

        target = get_object_or_404(User, pk=user_id)
        if not can_view_person(request.user, target):
            raise PermissionDenied()
        data = {"user": user_payload(target, request)}
        st = getattr(target, "student_profile", None)
        emp = getattr(target, "employee_profile", None)
        if st:
            summary = dict(StudentAttendance.objects.filter(student=st, subject__isnull=True)
                           .values_list("status").annotate(c=Count("id")))
            total = sum(summary.values())
            present = summary.get("present", 0) + summary.get("late", 0) + summary.get("half_day", 0) * 0.5
            invoices = Invoice.objects.filter(student=st).exclude(status="cancelled")
            agg = invoices.aggregate(total=Sum("total"), paid=Sum("paid_amount"))
            data["student"] = {
                "id": st.id, "admission_no": st.admission_no, "roll_no": st.roll_no, "status": st.get_status_display(),
                "section": str(st.section) if st.section else None, "department": str(st.department) if st.department else None,
                "admission_date": st.admission_date, "is_boarder": st.is_boarder, "is_orphan": st.is_orphan,
                "blood_group": st.blood_group, "mother_name": st.mother_name, "previous_institution": st.previous_institution,
                "guardian": {"name": st.guardian.name, "phone": st.guardian.phone,
                             "relation": st.guardian.get_relation_display()} if st.guardian else None,
                "medical_notes": st.medical_notes,
            }
            data["attendance"] = {"summary": summary, "total": total,
                                  "percentage": round(present / total * 100, 1) if total else None}
            data["fees"] = {"total": agg["total"] or 0, "paid": agg["paid"] or 0,
                            "balance": (agg["total"] or 0) - (agg["paid"] or 0),
                            "invoices": _rows(invoices[:24], ["id", "invoice_no", "title", "total", "paid_amount", "status", "due_date"])}
            data["marks"] = _rows(Mark.objects.filter(student=st).select_related("paper__exam", "paper__subject")
                                  .order_by("-paper__date")[:60],
                                  ["paper.exam.name", "paper.subject.name", "marks_obtained", "paper.max_marks", "is_absent"])
            juz = JuzProgress.objects.filter(student=st, program="hifz")
            data["hifz"] = {"memorized": juz.filter(status__in=["memorized", "tested"]).count(),
                            "juz": _rows(juz, ["juz", "status", "completed_on", "test_score"])}
            from hifz.services import overview as quran_overview
            data["quran"] = quran_overview(st)
            data["hostel"] = _rows(HostelAllocation.objects.filter(student=st), ["room", "bed_no", "from_date", "to_date", "is_active"])
            data["promotions"] = _rows(st.promotions.all(), ["date", "from_section", "to_section", "result"])
        if emp:
            summary = dict(StaffAttendance.objects.filter(employee=emp).values_list("status").annotate(c=Count("id")))
            data["employee"] = {
                "id": emp.id, "employee_no": emp.employee_no, "designation": emp.designation, "kind": emp.get_kind_display(),
                "department": str(emp.department) if emp.department else None, "status": emp.get_status_display(),
                "employment_type": emp.get_employment_type_display(), "joining_date": emp.joining_date,
                "qualification": emp.highest_qualification, "specialization": emp.specialization, "ijazah": emp.ijazah,
                "experience_years": emp.experience_years,
            }
            if has_role(request.user, HR + [R.ACCOUNTANT]) or request.user.id == target.id:
                data["employee"]["basic_salary"] = emp.basic_salary
                data["payslips"] = _rows(Payslip.objects.filter(employee=emp)[:24], ["id", "month", "net", "status", "paid_on"])
            data["attendance"] = {"summary": summary, "total": sum(summary.values())}
            data["history"] = _rows(emp.history.all(), ["organization", "position", "from_date", "to_date"])
            data["teaching"] = [str(a) for a in target.teaching_assignments.select_related("subject", "section")]
        data["leaves"] = _rows(LeaveRequest.objects.filter(user=target)[:30], ["id", "leave_type", "start_date", "end_date", "status", "reason"])
        data["qualifications"] = _rows(target.qualifications.all(), ["title", "institution", "year", "grade"])
        data["documents"] = [{"title": d.title, "kind": d.get_kind_display(),
                              "url": request.build_absolute_uri(d.file.url) if d.file else None} for d in target.documents.all()]
        data["disciplinary"] = _rows(target.disciplinary_records.all(), ["date", "severity", "incident", "action_taken"])
        data["medical"] = _rows(target.medical_records.all(), ["date", "condition", "treatment"])
        data["achievements"] = _rows(target.achievements.all(), ["date", "title", "category"])
        data["certificates"] = _rows(Certificate.objects.filter(person=target), ["id", "serial_no", "title", "issue_date"])
        data["library"] = _rows(BookIssue.objects.filter(borrower=target)[:30],
                                ["book", "issued_on", "due_date", "returned_on", "status", "fine"])
        data["transport"] = _rows(TransportAssignment.objects.filter(user=target, is_active=True), ["route", "stop"])
        return Response(data)


class MyChildrenView(APIView):
    def get(self, request):
        return Response([{"id": x.id, "user_id": x.user_id, "name": x.user.display_name, "admission_no": x.admission_no,
                          "section": str(x.section) if x.section else None, "section_id": x.section_id}
                         for x in children_qs(request.user).select_related("user", "section")])


class SectionRosterView(APIView):
    def get(self, request, section_id):
        if not (has_role(request.user, STUDENT_VIEWERS) or section_id in teacher_section_ids(request.user)):
            raise PermissionDenied()
        qs = Student.objects.filter(section_id=section_id, status="active").select_related("user")
        return Response([{"id": x.id, "user_id": x.user_id, "name": x.user.display_name, "admission_no": x.admission_no,
                          "roll_no": x.roll_no, "father_name": x.user.father_name} for x in qs])
