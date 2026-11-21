from decimal import Decimal

from django.db.models import Q

from core.roles import EXAM, R, has_role, is_admin
from core.scopes import teacher_section_ids, visible_student_ids
from people.models import Student

from .models import GradeScale, Mark


def paper_scope(qs, user):
    if user.role == R.TEACHER:
        return qs.filter(Q(section_id__in=teacher_section_ids(user)) | Q(examiner=user) | Q(invigilator=user))
    sections = Student.objects.filter(id__in=visible_student_ids(user)).values_list("section_id", flat=True)
    return qs.filter(section_id__in=sections)


def mark_scope(qs, user):
    if user.role == R.TEACHER:
        return qs.filter(Q(paper__section_id__in=teacher_section_ids(user)) | Q(paper__examiner=user))
    return qs.filter(student_id__in=visible_student_ids(user), paper__exam__is_published=True)


def can_enter_marks(user, paper):
    if is_admin(user) or has_role(user, EXAM):
        return True
    if paper.marks_locked:
        return False
    from academics.models import TeacherAssignment
    return (paper.examiner_id == user.id or paper.section.class_teacher_id == user.id
            or TeacherAssignment.objects.filter(teacher=user, section=paper.section, subject=paper.subject).exists())


def compute_result(exam, section):
    """Tabulated result of a section: totals, percentage, grade, pass/fail and position."""
    papers = list(exam.papers.filter(section=section).select_related("subject").order_by("subject__name"))
    marks = {(m.student_id, m.paper_id): m for m in Mark.objects.filter(paper__in=papers)}
    students = list(section.students.exclude(status="left").select_related("user"))
    scales = list(GradeScale.objects.all())

    def grade_for(pct):
        return next((g for g in scales if g.min_percentage <= pct <= g.max_percentage), None)

    rows = []
    for st in students:
        total = max_total = Decimal(0)
        subjects, failed = [], False
        for p in papers:
            m = marks.get((st.id, p.id))
            obtained = m.marks_obtained if m and m.marks_obtained is not None else None
            max_total += p.max_marks
            total += obtained or 0
            passed = obtained is not None and obtained >= p.pass_marks
            failed = failed or not passed
            subjects.append({"paper": p.id, "subject": p.subject.name, "book": p.subject.book, "max": p.max_marks,
                             "pass": p.pass_marks, "obtained": obtained, "absent": bool(m and m.is_absent), "passed": passed})
        pct = (total / max_total * 100).quantize(Decimal("0.01")) if max_total else Decimal(0)
        g = grade_for(pct)
        rows.append({"student": st.id, "user_id": st.user_id, "name": st.user.display_name,
                     "father_name": st.user.father_name, "admission_no": st.admission_no, "roll_no": st.roll_no,
                     "subjects": subjects, "total": total, "max_total": max_total, "percentage": pct,
                     "grade": g.name if g else "-", "remarks": g.remarks if g else "",
                     "result": "Fail" if failed or (g and not g.is_pass) else "Pass"})
    pos, last = 0, None
    for i, r in enumerate(sorted(rows, key=lambda r: -r["percentage"]), 1):
        if r["percentage"] != last:
            pos, last = i, r["percentage"]
        r["position"] = pos if r["result"] == "Pass" else None
    return {"exam": {"id": exam.id, "name": exam.name, "kind": exam.get_kind_display(), "year": str(exam.academic_year),
                     "is_published": exam.is_published},
            "section": {"id": section.id, "label": str(section)},
            "subjects": [{"paper": p.id, "subject": p.subject.name, "max": p.max_marks} for p in papers],
            "rows": rows,
            "stats": {"students": len(rows), "passed": sum(r["result"] == "Pass" for r in rows),
                      "average": round(sum(r["percentage"] for r in rows) / len(rows), 2) if rows else 0}}
