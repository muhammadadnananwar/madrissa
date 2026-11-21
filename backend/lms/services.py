"""Who can see / teach which course."""
from django.db.models import Q

from core.roles import ACADEMIC, R, has_role, is_admin
from core.scopes import children_qs

from .models import Course


def student_course_ids(student_user):
    sp = getattr(student_user, "student_profile", None)
    q = Q(enrollments__student=student_user) | Q(enrollment_type=Course.Enrollment.OPEN)
    if sp and sp.section_id:
        q |= Q(section_id=sp.section_id, enrollment_type=Course.Enrollment.SECTION)
    return set(Course.objects.filter(q, is_published=True).values_list("id", flat=True))


def visible_course_ids(user):
    """None means 'all courses'."""
    if is_admin(user) or has_role(user, ACADEMIC):
        return None
    if user.role == R.TEACHER:
        return set(Course.objects.filter(Q(teacher=user) | Q(co_teachers=user)).values_list("id", flat=True))
    if user.role == R.STUDENT:
        return student_course_ids(user)
    if user.role == R.PARENT:
        ids = set()
        for st in children_qs(user).select_related("user"):
            ids |= student_course_ids(st.user)
        return ids
    return set()


def teaches(user, course):
    return (is_admin(user) or has_role(user, ACADEMIC) or course.teacher_id == user.id
            or course.co_teachers.filter(pk=user.pk).exists())


def is_participant(user, course):
    ids = visible_course_ids(user)
    return ids is None or course.id in ids


def course_scope(path=None):
    """Scope function for viewsets whose rows belong to a course (path = lookup to course id)."""
    def scope(qs, user):
        ids = visible_course_ids(user)
        if ids is None:
            return qs
        qs = qs.filter(**{f"{path}__in": ids}) if path else qs.filter(id__in=ids)
        if user.role in (R.STUDENT, R.PARENT) and "is_published" in {f.name for f in qs.model._meta.fields}:
            qs = qs.filter(is_published=True)
        return qs
    return scope


def course_of(instance_or_data):
    """Resolve the course for a lesson/module/quiz/question/choice/thread (instance or validated data)."""
    get = instance_or_data.get if isinstance(instance_or_data, dict) else lambda k: getattr(instance_or_data, k, None)
    if get("course"):
        return get("course")
    if get("module"):
        return get("module").course
    if get("quiz"):
        return get("quiz").course
    if get("question"):
        return get("question").quiz.course
    if get("thread"):
        return get("thread").course
    return None
