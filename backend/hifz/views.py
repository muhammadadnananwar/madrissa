from datetime import datetime, timedelta

from django.db import transaction
from django.db.models import Avg, Count, Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from core.roles import ACADEMIC, ALL, R, STUDENT_VIEWERS, has_role
from core.scopes import by_student, teacher_section_ids, visible_student_ids
from core.viewsets import BaseModelViewSet
from people.models import Student

from . import serializers as s
from . import services
from .models import (ChecklistItem, HifzRecord, JuzProgress, QaidaLesson, QaidaProgress, Quality, QuranCompletion,
                     StudentChecklist, TarjumaProgress)
from .quran import SURAH_CHOICES

G = "Quran Programs"
TEACHERS = ACADEMIC + [R.TEACHER]
ENTRY_FIELDS = ["sabaq_surah", "sabaq_from_ayah", "sabaq_to_ayah", "sabaq_lines", "sabaq_quality", "sabqi_juz",
                "sabqi_quantity", "sabqi_quality", "manzil_juz", "manzil_quality", "mistakes", "hesitations",
                "tajweed_rating", "remarks"]


def check_section(user, section_id):
    if not (has_role(user, ACADEMIC) or int(section_id) in teacher_section_ids(user)):
        raise PermissionDenied()


class HifzRecordViewSet(BaseModelViewSet):
    queryset = HifzRecord.objects.all()
    serializer_class = s.HifzRecordSerializer
    resource_key = "hifz-records"
    read_roles, write_roles = ACADEMIC, TEACHERS
    scope = by_student()
    filterset_fields = ["date", "student", "program", "teacher", "student__section"]
    label, group, icon, menu = "Daily Hifz Records", G, "quran", False
    list_fields = ["date", "student", "program", "sabaq_surah", "sabaq_quality", "sabqi_quality", "manzil_quality", "mistakes"]

    def validate_create(self, serializer, extra):
        st = serializer.validated_data["student"]
        user = self.request.user
        if user.role == R.TEACHER and st.section_id not in teacher_section_ids(user):
            raise PermissionDenied("This student is not in your halqa.")
        if not serializer.validated_data.get("teacher"):
            extra["teacher"] = user


class JuzProgressViewSet(BaseModelViewSet):
    queryset = JuzProgress.objects.all()
    serializer_class = s.JuzProgressSerializer
    resource_key = "juz-progress"
    read_roles, write_roles = ACADEMIC, TEACHERS
    scope = by_student()
    filterset_fields = ["student", "program", "status", "juz", "student__section"]
    label, group, icon, menu = "Para (Juz) Progress", G, "bar", False
    list_fields = ["student", "juz", "status", "completed_on", "test_score", "tested_by"]


class DailySheetView(APIView):
    """Daily sabaq / sabqi / manzil entry for a whole halqa."""

    def get(self, request):
        section = request.query_params.get("section")
        check_section(request.user, section)
        d = datetime.strptime(request.query_params["date"], "%Y-%m-%d").date() if request.query_params.get("date") \
            else timezone.localdate()
        program = request.query_params.get("program") or "hifz"
        existing = {h.student_id: h for h in HifzRecord.objects.filter(student__section_id=section, date=d, program=program)}
        last = {}
        for h in HifzRecord.objects.filter(student__section_id=section, date__lt=d, program=program).order_by("student_id", "-date"):
            last.setdefault(h.student_id, h)
        rows = []
        for st in Student.objects.filter(section_id=section, status="active").select_related("user"):
            h, prev = existing.get(st.id), last.get(st.id)
            row = {"student": st.id, "name": st.user.display_name, "admission_no": st.admission_no}
            row.update({f: getattr(h, f) if h else None for f in ENTRY_FIELDS})
            row["previous"] = {"date": prev.date, "sabaq_surah": prev.sabaq_surah, "sabaq_to_ayah": prev.sabaq_to_ayah,
                               "sabqi_juz": prev.sabqi_juz} if prev else None
            rows.append(row)
        return Response({"date": d, "program": program, "rows": rows,
                         "surahs": [{"value": v, "label": l} for v, l in SURAH_CHOICES],
                         "qualities": [{"value": v, "label": l} for v, l in Quality.choices]})

    @transaction.atomic
    def post(self, request):
        ser = s.DailySheetSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        check_section(request.user, d["section"])
        valid = set(Student.objects.filter(section_id=d["section"]).values_list("id", flat=True))
        n = 0
        for r in d["records"]:
            if r["student"] not in valid:
                continue
            vals = {f: r.get(f) for f in ENTRY_FIELDS if f in r}
            if not any(v not in (None, "", 0) for v in vals.values()):
                continue
            HifzRecord.objects.update_or_create(student_id=r["student"], date=d["date"], program=d["program"],
                                                defaults={**vals, "teacher": request.user})
            n += 1
        return Response({"detail": f"Saved {n} record(s).", "count": n})


class StudentHifzSummaryView(APIView):
    def get(self, request, student_id):
        st = get_object_or_404(Student.objects.select_related("user", "section"), pk=student_id)
        if not (has_role(request.user, STUDENT_VIEWERS) or st.id in visible_student_ids(request.user)):
            raise PermissionDenied()
        juz = {j.juz: j for j in JuzProgress.objects.filter(student=st, program="hifz")}
        grid = [{"juz": i, "status": juz[i].status if i in juz else "not_started",
                 "completed_on": juz[i].completed_on if i in juz else None,
                 "test_score": juz[i].test_score if i in juz else None} for i in range(1, 31)]
        recent = HifzRecord.objects.filter(student=st).select_related("teacher").order_by("-date")
        month = recent.filter(date__gte=timezone.localdate() - timedelta(days=30))
        agg = month.aggregate(days=Count("id"), mistakes=Sum("mistakes"), lines=Sum("sabaq_lines"), tajweed=Avg("tajweed_rating"))
        quality = dict(month.values_list("sabaq_quality").annotate(c=Count("id")))
        memorized = sum(1 for g in grid if g["status"] in ("memorized", "tested"))
        records = []
        for h in recent[:60]:
            sabaq = ""
            if h.sabaq_surah:
                sabaq = f"{h.get_sabaq_surah_display()} {h.sabaq_from_ayah or ''}-{h.sabaq_to_ayah or ''}".strip(" -")
            elif h.sabaq_lines:
                sabaq = f"{h.sabaq_lines} lines"
            records.append({"date": h.date, "program": h.get_program_display(), "sabaq": sabaq,
                            "sabaq_quality": h.get_sabaq_quality_display(),
                            "sabqi": f"Para {h.sabqi_juz} {h.sabqi_quantity}".strip() if h.sabqi_juz else "",
                            "sabqi_quality": h.get_sabqi_quality_display(), "manzil": h.manzil_juz,
                            "manzil_quality": h.get_manzil_quality_display(), "mistakes": h.mistakes,
                            "hesitations": h.hesitations, "tajweed": h.tajweed_rating, "remarks": h.remarks,
                            "teacher": h.teacher.display_name if h.teacher else ""})
        return Response({"student": {"id": st.id, "name": st.user.display_name, "section": str(st.section) if st.section else ""},
                         "memorized": memorized, "percentage": round(memorized / 30 * 100, 1), "grid": grid,
                         "last_30_days": {**agg, "quality": quality}, "records": records})


def _student_for_teacher(request, student_id):
    st = get_object_or_404(Student.objects.select_related("user", "section"), pk=student_id)
    if not (has_role(request.user, ACADEMIC) or st.section_id in teacher_section_ids(request.user)):
        raise PermissionDenied()
    return st


class SetJuzView(APIView):
    """Update one para of a student's Hifz / Nazra / Tarjuma grid."""

    def post(self, request, student_id):
        st = _student_for_teacher(request, student_id)
        ser = s.SetJuzSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        services.set_para(st, d["program"], d["juz"], d["status"], request.user, d.get("test_score"))
        return Response({"detail": "Updated.", **services.para_grid(st, d["program"])})


class SetQaidaView(APIView):
    def post(self, request, student_id):
        st = _student_for_teacher(request, student_id)
        ser = s.SetQaidaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        services.set_qaida(st, d["lesson"], d["status"], request.user, d["remarks"])
        return Response({"detail": "Updated.", **services.qaida_summary(st)})


class SetTarjumaView(APIView):
    def post(self, request, student_id):
        st = _student_for_teacher(request, student_id)
        ser = s.SetTarjumaSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        services.set_tarjuma(st, d["surah"], d["status"], request.user, d.get("ayahs_done"), d.get("test_score"), d["remarks"])
        summary = services.tarjuma_summary(st)
        return Response({"detail": "Updated.", "percentage": summary["percentage"], "completed": summary["completed"]})


class SetChecklistView(APIView):
    def post(self, request, student_id):
        st = _student_for_teacher(request, student_id)
        ser = s.SetChecklistSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        services.set_checklist(st, d["item"], d["status"], request.user, d.get("score"), d["remarks"])
        return Response({"detail": "Updated."})


class RecordKhatmView(APIView):
    """Manually record a completion (e.g. a Dor / revision cycle, or a khatm before the system was used)."""

    def post(self, request, student_id):
        st = _student_for_teacher(request, student_id)
        ser = s.RecordKhatmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        c = services.record_completion(st, d["kind"], request.user, d["remarks"], d.get("started_on"))
        if d.get("completed_on"):
            c.completed_on = d["completed_on"]
            c.save(update_fields=["completed_on"])
        return Response({"detail": f"{c.get_kind_display()} #{c.number} recorded."})


class StudentProgramsView(APIView):
    """Everything about a student's Quran education: Qaida, Nazra, Hifz, Tarjuma, checklists, khatms."""

    def get(self, request, student_id):
        st = get_object_or_404(Student.objects.select_related("user", "section"), pk=student_id)
        if not (has_role(request.user, STUDENT_VIEWERS) or st.id in visible_student_ids(request.user)):
            raise PermissionDenied()
        can_edit = has_role(request.user, ACADEMIC) or st.section_id in teacher_section_ids(request.user)
        return Response({
            "student": {"id": st.id, "name": st.user.display_name, "section": str(st.section) if st.section else ""},
            "can_edit": can_edit,
            "qaida": services.qaida_summary(st),
            "nazra": services.para_grid(st, "nazra"),
            "hifz": services.para_grid(st, "hifz"),
            "tarjuma": services.tarjuma_summary(st),
            "checklists": services.checklist_summary(st),
            "khatms": [{"kind": k.kind, "kind_display": k.get_kind_display(), "number": k.number, "started_on": k.started_on,
                        "completed_on": k.completed_on, "remarks": k.remarks} for k in st.quran_completions.all()],
        })


class ChecklistSheetView(APIView):
    """Mark one checklist item (e.g. a dua) for a whole section at once."""

    def get(self, request):
        section = request.query_params.get("section")
        check_section(request.user, section)
        item = get_object_or_404(ChecklistItem, pk=request.query_params.get("item"))
        done = {c.student_id: c for c in StudentChecklist.objects.filter(item=item, student__section_id=section)}
        return Response({"item": {"id": item.id, "title": item.title, "arabic": item.arabic, "translation": item.translation,
                                  "reference": item.reference, "category": item.get_category_display()},
                         "rows": [{"student": x.id, "name": x.user.display_name,
                                   "status": done[x.id].status if x.id in done else "not_started",
                                   "score": done[x.id].score if x.id in done else None}
                                  for x in Student.objects.filter(section_id=section, status="active").select_related("user")]})

    @transaction.atomic
    def post(self, request):
        ser = s.ChecklistSheetSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        check_section(request.user, d["section"])
        valid = {x.id: x for x in Student.objects.filter(section_id=d["section"])}
        n = 0
        for r in d["records"]:
            if r["student"] in valid:
                services.set_checklist(valid[r["student"]], d["item"], r["status"], request.user, r.get("score"))
                n += 1
        return Response({"detail": f"Saved for {n} student(s)."})


class QaidaLessonViewSet(BaseModelViewSet):
    queryset = QaidaLesson.objects.all()
    serializer_class = s.QaidaLessonSerializer
    resource_key = "qaida-lessons"
    read_roles, write_roles = ALL, ACADEMIC
    label, group, icon = "Noorani Qaida Lessons", G, "book"
    list_fields = ["number", "title", "title_arabic"]


class QaidaProgressViewSet(BaseModelViewSet):
    queryset = QaidaProgress.objects.all()
    serializer_class = s.QaidaProgressSerializer
    resource_key = "qaida-progress"
    read_roles, write_roles = ACADEMIC, TEACHERS
    scope = by_student()
    filterset_fields = ["student", "lesson", "status", "student__section"]
    label, group, icon, menu = "Qaida Progress", G, "check", False
    list_fields = ["student", "lesson", "status", "passed_on", "checked_by"]


class TarjumaProgressViewSet(BaseModelViewSet):
    queryset = TarjumaProgress.objects.all()
    serializer_class = s.TarjumaProgressSerializer
    resource_key = "tarjuma-progress"
    read_roles, write_roles = ACADEMIC, TEACHERS
    scope = by_student()
    filterset_fields = ["student", "surah", "status", "student__section"]
    label, group, icon, menu = "Tarjuma Progress", G, "book", False
    list_fields = ["student", "surah", "status", "ayahs_done", "completed_on", "test_score"]


class QuranCompletionViewSet(BaseModelViewSet):
    queryset = QuranCompletion.objects.all()
    serializer_class = s.QuranCompletionSerializer
    resource_key = "khatm-register"
    read_roles, write_roles = ACADEMIC, TEACHERS
    scope = by_student()
    filterset_fields = ["student", "kind", "student__section", "completed_on"]
    label, group, icon = "Khatm Register", G, "award"
    list_fields = ["student", "kind", "number", "started_on", "completed_on", "recorded_by"]
    menu_roles = TEACHERS


class ChecklistItemViewSet(BaseModelViewSet):
    queryset = ChecklistItem.objects.all()
    serializer_class = s.ChecklistItemSerializer
    resource_key = "checklist-items"
    read_roles, write_roles = ALL, ACADEMIC
    search_fields = ["title", "translation", "reference"]
    filterset_fields = ["category", "is_active", "level"]
    label, group, icon = "Duas, Kalimas, Tajweed & Hadith", G, "list"
    list_fields = ["category", "title", "reference", "level", "order", "is_active"]
    menu_roles = TEACHERS


class StudentChecklistViewSet(BaseModelViewSet):
    queryset = StudentChecklist.objects.all()
    serializer_class = s.StudentChecklistSerializer
    resource_key = "student-checklist"
    read_roles, write_roles = ACADEMIC, TEACHERS
    scope = by_student()
    filterset_fields = ["student", "item", "item__category", "status", "student__section"]
    label, group, icon, menu = "Student Checklists", G, "check", False
    list_fields = ["student", "item", "status", "score", "date", "checked_by"]


class SectionHifzOverviewView(APIView):
    def get(self, request, section_id):
        check_section(request.user, section_id)
        rows = []
        for st in Student.objects.filter(section_id=section_id, status="active").select_related("user"):
            last = HifzRecord.objects.filter(student=st).order_by("-date").first()
            rows.append({"student": st.id, "name": st.user.display_name,
                         "memorized": JuzProgress.objects.filter(student=st, program="hifz", status__in=["memorized", "tested"]).count(),
                         "last_date": last.date if last else None,
                         "last_sabaq": last.get_sabaq_surah_display() if last and last.sabaq_surah else None})
        rows.sort(key=lambda r: -r["memorized"])
        return Response(rows)
