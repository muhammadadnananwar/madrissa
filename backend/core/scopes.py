"""Row-level visibility helpers: who may see which students / users."""
from django.db.models import Q

from .roles import Role


def teacher_section_ids(user):
    from academics.models import Section, TeacherAssignment, TimetableEntry
    ids = set(Section.objects.filter(class_teacher=user).values_list("id", flat=True))
    ids |= set(TeacherAssignment.objects.filter(teacher=user).values_list("section_id", flat=True))
    ids |= set(TimetableEntry.objects.filter(teacher=user).values_list("section_id", flat=True))
    return ids


def children_qs(user):
    from people.models import Student
    return Student.objects.filter(Q(guardian__user=user) | Q(second_guardian__user=user))


def visible_student_ids(user):
    """Student (profile) ids the user may see when not a full-access role."""
    from people.models import Student
    if user.role == Role.STUDENT:
        return set(Student.objects.filter(user=user).values_list("id", flat=True))
    if user.role == Role.PARENT:
        return set(children_qs(user).values_list("id", flat=True))
    if user.role == Role.TEACHER:
        return set(Student.objects.filter(section_id__in=teacher_section_ids(user)).values_list("id", flat=True))
    if user.role == Role.HOSTEL_WARDEN:
        return set(Student.objects.filter(is_boarder=True).values_list("id", flat=True))
    return set()


def visible_user_ids(user):
    """User ids whose personal records the user may see (self + students/children)."""
    from people.models import Student
    ids = {user.id}
    sids = visible_student_ids(user)
    if sids:
        ids |= set(Student.objects.filter(id__in=sids).values_list("user_id", flat=True))
    return ids


# --- ready-made scope functions for Resource(scope=...) ---------------------
def by_student(field="student"):
    lookup = "id__in" if field == "id" else f"{field}_id__in"

    def scope(qs, user):
        return qs.filter(**{lookup: visible_student_ids(user)})
    return scope


def by_user(field="user"):
    def scope(qs, user):
        return qs.filter(**{f"{field}_id__in": visible_user_ids(user)})
    return scope


def own(field="user"):
    def scope(qs, user):
        return qs.filter(**{f"{field}_id": user.id})
    return scope


def by_section(field="section"):
    def scope(qs, user):
        from people.models import Student
        if user.role == Role.TEACHER:
            ids = teacher_section_ids(user)
        else:
            ids = set(Student.objects.filter(id__in=visible_student_ids(user)).values_list("section_id", flat=True))
        return qs.filter(**{f"{field}_id__in": ids})
    return scope
