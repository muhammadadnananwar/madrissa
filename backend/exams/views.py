from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from academics.models import Section
from attendance.models import StudentAttendance
from attendance.services import attendance_percentage
from communication.services import notify
from core.audit import audit
from core.roles import ALL, EXAM, R, STUDENT_VIEWERS, has_role
from core.scopes import by_user, teacher_section_ids, visible_student_ids, visible_user_ids
from core.viewsets import BaseModelViewSet
from people.models import Student

from . import serializers as s
from .models import Certificate, Exam, ExamPaper, GradeScale, Mark
from .services import can_enter_marks, compute_result, mark_scope, paper_scope

G = "Examinations"


def _institution():
    from website.models import SiteSettings
    site = SiteSettings.get()
    return {"name": site.name, "name_arabic": site.name_arabic, "address": site.address, "affiliation": site.affiliation}


class GradeScaleViewSet(BaseModelViewSet):
    queryset = GradeScale.objects.all()
    serializer_class = s.GradeScaleSerializer
    resource_key = "grade-scales"
    read_roles, write_roles = ALL, EXAM
    label, group, icon = "Grading Scale", G, "percent"
    list_fields = ["name", "min_percentage", "max_percentage", "grade_point", "is_pass"]


class ExamViewSet(BaseModelViewSet):
    queryset = Exam.objects.all()
    serializer_class = s.ExamSerializer
    resource_key = "exams"
    read_roles, write_roles = ALL, EXAM
    group, icon = G, "clipboard"
    list_fields = ["name", "kind", "academic_year", "start_date", "end_date", "is_published"]
    ui_actions = [
        {"name": "publish", "label": "Publish / Unpublish results", "roles": EXAM, "confirm": "Toggle result publication?"},
        {"name": "lock_marks", "label": "Lock marks entry", "roles": EXAM, "confirm": "Lock all marks for this exam?"},
    ]

    @action(detail=True, methods=["post"])
    def publish(self, request, pk=None):
        exam = self.get_object()
        exam.is_published = not exam.is_published
        exam.save(update_fields=["is_published", "updated_at"])
        if exam.is_published:
            users = set()
            for p in exam.papers.select_related("section"):
                for st in p.section.students.filter(status="active").select_related("guardian__user", "user"):
                    users.add(st.user)
                    if st.guardian and st.guardian.user:
                        users.add(st.guardian.user)
            notify(list(users), f"Results published: {exam.name}", "View the report card in the portal.", "/exams/results", "result")
        audit(request, "publish" if exam.is_published else "unpublish", exam, "exams")
        return Response({"detail": "Results published." if exam.is_published else "Results unpublished.",
                         "is_published": exam.is_published})

    @action(detail=True, methods=["post"])
    def lock_marks(self, request, pk=None):
        exam = self.get_object()
        lock = bool(request.data.get("lock", True))
        exam.papers.update(marks_locked=lock)
        return Response({"detail": "Marks locked." if lock else "Marks unlocked."})


class ExamPaperViewSet(BaseModelViewSet):
    queryset = ExamPaper.objects.all()
    serializer_class = s.ExamPaperSerializer
    resource_key = "exam-papers"
    read_roles, write_roles = EXAM + [R.ADMISSION_OFFICER], EXAM
    scope = staticmethod(paper_scope)
    filterset_fields = ["exam", "section", "subject", "date", "examiner", "marks_locked"]
    label, group, icon, menu_roles = "Date Sheet / Papers", G, "calendar", ALL
    list_fields = ["exam", "section", "subject", "date", "start_time", "max_marks", "examiner", "marks_locked"]


class MarkViewSet(BaseModelViewSet):
    queryset = Mark.objects.all()
    serializer_class = s.MarkSerializer
    resource_key = "marks"
    read_roles = write_roles = EXAM
    scope = staticmethod(mark_scope)
    filterset_fields = ["paper", "student", "paper__exam", "paper__section"]
    group, icon, menu = G, "edit", False
    list_fields = ["paper", "student", "marks_obtained", "is_absent", "entered_by"]


class CertificateViewSet(BaseModelViewSet):
    queryset = Certificate.objects.all()
    serializer_class = s.CertificateSerializer
    resource_key = "certificates"
    read_roles = EXAM + [R.HR_MANAGER, R.ADMISSION_OFFICER]
    write_roles = EXAM + [R.HR_MANAGER]
    scope = by_user("person")
    search_fields = ["serial_no", "title", "person__first_name", "person__last_name"]
    label, group, icon, menu_roles = "Certificates & Asnaad", G, "award", ALL
    list_fields = ["serial_no", "person", "kind", "title", "issue_date", "is_revoked"]


# ------------------------------------------------------------------ APIViews
class MarksSheetView(APIView):
    """GET / POST marks for every student of a paper."""

    def _paper(self, request, paper_id):
        paper = get_object_or_404(ExamPaper.objects.select_related("exam", "section", "subject"), pk=paper_id)
        if not can_enter_marks(request.user, paper):
            raise PermissionDenied("You cannot enter marks for this paper (not assigned or locked).")
        return paper

    def get(self, request, paper_id):
        paper = self._paper(request, paper_id)
        existing = {m.student_id: m for m in paper.marks.all()}
        rows = []
        for st in paper.section.students.filter(status="active").select_related("user"):
            m = existing.get(st.id)
            rows.append({"student": st.id, "name": st.user.display_name, "admission_no": st.admission_no,
                         "roll_no": st.roll_no, "marks_obtained": m.marks_obtained if m else None,
                         "is_absent": m.is_absent if m else False, "remarks": m.remarks if m else ""})
        return Response({"paper": {"id": paper.id, "label": str(paper), "max_marks": paper.max_marks,
                                   "pass_marks": paper.pass_marks, "locked": paper.marks_locked, "date": paper.date},
                         "rows": rows})

    @transaction.atomic
    def post(self, request, paper_id):
        paper = self._paper(request, paper_id)
        ser = s.MarksSheetSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        valid = set(Student.objects.filter(section=paper.section).values_list("id", flat=True))
        n = 0
        for r in ser.validated_data["records"]:
            if r["student"] not in valid:
                continue
            val = None if r["is_absent"] else r.get("marks_obtained")
            if val is not None and val > paper.max_marks:
                raise ValidationError({"detail": f"Marks must be between 0 and {paper.max_marks}."})
            Mark.objects.update_or_create(paper=paper, student_id=r["student"], defaults={
                "marks_obtained": val, "is_absent": r["is_absent"], "remarks": r["remarks"], "entered_by": request.user})
            n += 1
        audit(request, "marks_entry", paper, "marks", {"count": n})
        return self.get(request, paper_id)


class SectionResultView(APIView):
    def get(self, request):
        exam = get_object_or_404(Exam, pk=request.query_params.get("exam"))
        section = get_object_or_404(Section, pk=request.query_params.get("section"))
        if not (has_role(request.user, STUDENT_VIEWERS) or section.id in teacher_section_ids(request.user)):
            raise PermissionDenied()
        return Response(compute_result(exam, section))


class ReportCardView(APIView):
    """?student=<id>&exam=<id> (exam optional → all exams of the student)."""

    def get(self, request):
        student = get_object_or_404(Student.objects.select_related("user", "section"), pk=request.query_params.get("student"))
        user = request.user
        staff_view = has_role(user, STUDENT_VIEWERS) or student.section_id in teacher_section_ids(user)
        if not staff_view and student.id not in visible_student_ids(user):
            raise PermissionDenied()
        exams = Exam.objects.filter(papers__marks__student=student).distinct()
        if request.query_params.get("exam"):
            exams = exams.filter(pk=request.query_params["exam"])
        if not staff_view:
            exams = exams.filter(is_published=True)
        cards = []
        for exam in exams:
            section_ids = exam.papers.filter(marks__student=student).values_list("section_id", flat=True).distinct()
            for sec in Section.objects.filter(id__in=section_ids):
                res = compute_result(exam, sec)
                row = next((r for r in res["rows"] if r["student"] == student.id), None)
                if row:
                    cards.append({"exam": res["exam"], "section": res["section"], "result": row,
                                  "class_size": res["stats"]["students"]})
        summary = dict(StudentAttendance.objects.filter(student=student, subject__isnull=True)
                       .values_list("status").annotate(c=Count("id")))
        return Response({"institution": _institution(),
                         "student": {"id": student.id, "name": student.user.display_name,
                                     "father_name": student.user.father_name, "admission_no": student.admission_no,
                                     "roll_no": student.roll_no, "section": str(student.section) if student.section else ""},
                         "attendance_percentage": attendance_percentage(summary), "cards": cards})


class MyExamsView(APIView):
    """Date sheet relevant to the current user."""

    def get(self, request):
        qs = ExamPaper.objects.select_related("exam", "section", "subject", "room")
        if not has_role(request.user, STUDENT_VIEWERS):
            qs = paper_scope(qs, request.user)
        if request.query_params.get("exam"):
            qs = qs.filter(exam_id=request.query_params["exam"])
        else:
            qs = qs.filter(exam__academic_year__is_current=True)
        return Response([{"id": p.id, "exam": p.exam.name, "exam_id": p.exam_id, "section": str(p.section),
                          "section_id": p.section_id, "subject": p.subject.name, "date": p.date,
                          "start_time": p.start_time, "end_time": p.end_time, "room": str(p.room) if p.room else "",
                          "max_marks": p.max_marks, "locked": p.marks_locked, "is_published": p.exam.is_published,
                          "can_enter": can_enter_marks(request.user, p)} for p in qs.order_by("date", "start_time")[:500]])


class CertificatePrintView(APIView):
    def get(self, request, pk):
        c = get_object_or_404(Certificate.objects.select_related("person"), pk=pk)
        if not (has_role(request.user, EXAM + [R.HR_MANAGER, R.ADMISSION_OFFICER]) or c.person_id in visible_user_ids(request.user)):
            raise PermissionDenied()
        return Response({"serial_no": c.serial_no, "verification_code": c.verification_code, "title": c.title,
                         "kind": c.get_kind_display(), "issue_date": c.issue_date, "details": c.details, "grade": c.grade,
                         "is_revoked": c.is_revoked, "person": c.person.display_name, "father_name": c.person.father_name,
                         "institution": _institution()})
