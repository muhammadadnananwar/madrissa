import random
from datetime import timedelta

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from communication.services import notify
from core.roles import ACADEMIC, ALL, R
from core.scopes import by_section, children_qs
from core.viewsets import BaseModelViewSet

from . import serializers as s
from .models import (Assignment, AttemptAnswer, Choice, Course, CourseEnrollment, DiscussionReply, DiscussionThread,
                     Homework, Lesson, LessonProgress, Module, Question, Quiz, QuizAttempt, Submission)
from .services import course_of, course_scope, is_participant, student_course_ids, teaches, visible_course_ids

G = "Learning (LMS)"
MANAGERS = ACADEMIC + [R.TEACHER]


class LmsBase(BaseModelViewSet):
    read_roles = ACADEMIC
    write_roles = MANAGERS
    group = G
    menu = False


class CourseContentViewSet(LmsBase):
    """Teachers may only add/edit content in courses they teach."""

    def validate_create(self, serializer, extra):
        course = course_of(serializer.validated_data)
        if course is not None and not teaches(self.request.user, course):
            raise PermissionDenied("You do not teach this course.")

    def perform_update(self, serializer):
        course = course_of(serializer.instance)
        if course is not None and not teaches(self.request.user, course):
            raise PermissionDenied("You do not teach this course.")
        super().perform_update(serializer)


# ------------------------------------------------------------------ courses
class CourseViewSet(LmsBase):
    queryset = Course.objects.all()
    serializer_class = s.CourseSerializer
    resource_key = "courses"
    scope = course_scope()
    search_fields = ["title", "code", "description"]
    icon = "graduation"
    list_fields = ["title", "code", "teacher", "section", "subject", "enrollment_type", "is_published"]
    ui_actions = [{"name": "outline", "roles": ALL, "row": False}, {"name": "enroll", "roles": [R.STUDENT], "row": False},
                  {"name": "gradebook", "roles": MANAGERS, "row": False}]

    def validate_create(self, serializer, extra):
        if self.request.user.role == R.TEACHER or not serializer.validated_data.get("teacher"):
            extra["teacher"] = self.request.user

    @action(detail=True, methods=["get"])
    def outline(self, request, pk=None):
        course = get_object_or_404(Course.objects.select_related("teacher", "subject", "section"), pk=pk)
        user = request.user
        manager = teaches(user, course)
        if not manager and not is_participant(user, course):
            if not (course.enrollment_type == Course.Enrollment.OPEN and user.role == R.STUDENT):
                raise PermissionDenied()
        learner = request.query_params.get("student") if manager or user.role == R.PARENT else None
        learner_id = int(learner) if learner else (user.id if user.role == R.STUDENT else None)
        if user.role == R.PARENT:
            kids = set(children_qs(user).values_list("user_id", flat=True))
            learner_id = learner_id if learner_id in kids else (next(iter(kids)) if kids else None)
        now = timezone.now()
        done = set(LessonProgress.objects.filter(student_id=learner_id, lesson__module__course=course)
                   .values_list("lesson_id", flat=True)) if learner_id else set()

        modules, total = [], 0
        for m in course.modules.prefetch_related("lessons"):
            lessons = []
            for l in m.lessons.all():
                if not manager and (not l.is_published or (l.release_at and l.release_at > now)):
                    continue
                total += 1
                lessons.append({"id": l.id, "title": l.title, "kind": l.kind, "duration_minutes": l.duration_minutes,
                                "content": l.content, "media_url": l.media_url, "is_published": l.is_published,
                                "file": request.build_absolute_uri(l.file.url) if l.file else None,
                                "release_at": l.release_at, "completed": l.id in done})
            modules.append({"id": m.id, "title": m.title, "description": m.description, "order": m.order, "lessons": lessons})

        subs = {x.assignment_id: x for x in Submission.objects.filter(student_id=learner_id, assignment__course=course)} \
            if learner_id else {}
        assignments = []
        for a in course.assignments.all():
            if not manager and not a.is_published:
                continue
            item = {"id": a.id, "title": a.title, "instructions": a.instructions, "due_at": a.due_at,
                    "max_marks": a.max_marks, "allow_late": a.allow_late, "overdue": a.due_at < now,
                    "attachment": request.build_absolute_uri(a.attachment.url) if a.attachment else None}
            sub = subs.get(a.id)
            if sub:
                item["submission"] = {"id": sub.id, "status": sub.status, "marks": sub.marks, "feedback": sub.feedback,
                                      "submitted_at": sub.created_at, "text": sub.text,
                                      "file": request.build_absolute_uri(sub.file.url) if sub.file else None}
            if manager:
                item["submission_count"] = a.submissions.count()
                item["ungraded"] = a.submissions.exclude(status="graded").count()
            assignments.append(item)

        quizzes = []
        for q in course.quizzes.all():
            if not manager and not q.is_published:
                continue
            attempts = list(QuizAttempt.objects.filter(quiz=q, student_id=learner_id)) if learner_id else []
            quizzes.append({"id": q.id, "title": q.title, "description": q.description,
                            "time_limit_minutes": q.time_limit_minutes, "max_attempts": q.max_attempts,
                            "pass_percentage": q.pass_percentage, "available_from": q.available_from,
                            "available_until": q.available_until, "question_count": q.questions.count(),
                            "attempts": [{"id": t.id, "status": t.status, "score": t.score, "max_score": t.max_score,
                                          "passed": t.passed, "submitted_at": t.submitted_at} for t in attempts]})
        live = [{"id": l.id, "title": l.title, "scheduled_start": l.scheduled_start, "status": l.status,
                 "provider": l.provider, "recording_url": l.recording_url} for l in course.live_classes.all()[:20]]
        return Response({
            "course": {"id": course.id, "title": course.title, "code": course.code, "description": course.description,
                       "teacher": course.teacher.display_name, "subject": str(course.subject) if course.subject else None,
                       "section": str(course.section) if course.section else None,
                       "cover": request.build_absolute_uri(course.cover.url) if course.cover else None,
                       "enrollment_type": course.enrollment_type},
            "is_manager": manager, "learner": learner_id,
            "progress": round(len(done) / total * 100) if total else 0,
            "modules": modules, "assignments": assignments, "quizzes": quizzes, "live_classes": live,
        })

    @action(detail=True, methods=["post"])
    def enroll(self, request, pk=None):
        course = get_object_or_404(Course, pk=pk)
        if course.enrollment_type != Course.Enrollment.OPEN:
            raise PermissionDenied("Self enrolment is not allowed for this course.")
        CourseEnrollment.objects.get_or_create(course=course, student=request.user)
        return Response({"detail": "Enrolled."})

    @action(detail=True, methods=["get"])
    def gradebook(self, request, pk=None):
        course = self.get_object()
        if not teaches(request.user, course):
            raise PermissionDenied()
        students = list(course.student_users())
        assignments = list(course.assignments.all())
        quizzes = list(course.quizzes.all())
        lesson_count = Lesson.objects.filter(module__course=course).count()
        subs = {(x.student_id, x.assignment_id): x for x in Submission.objects.filter(assignment__course=course)}
        best = {}
        for t in QuizAttempt.objects.filter(quiz__course=course).exclude(status="in_progress"):
            k = (t.student_id, t.quiz_id)
            if k not in best or t.score > best[k].score:
                best[k] = t
        progress = {}
        for sid in LessonProgress.objects.filter(lesson__module__course=course).values_list("student_id", flat=True):
            progress[sid] = progress.get(sid, 0) + 1
        rows = [{
            "student": u.id, "name": u.display_name,
            "progress": round(progress.get(u.id, 0) / lesson_count * 100) if lesson_count else 0,
            "assignments": [getattr(subs.get((u.id, a.id)), "marks", None) for a in assignments],
            "assignment_status": [getattr(subs.get((u.id, a.id)), "status", "missing") for a in assignments],
            "quizzes": [getattr(best.get((u.id, q.id)), "score", None) for q in quizzes],
        } for u in students]
        return Response({"assignments": [{"id": a.id, "title": a.title, "max": a.max_marks} for a in assignments],
                         "quizzes": [{"id": q.id, "title": q.title} for q in quizzes], "rows": rows})


class CourseEnrollmentViewSet(CourseContentViewSet):
    queryset = CourseEnrollment.objects.all()
    serializer_class = s.CourseEnrollmentSerializer
    resource_key = "course-enrollments"
    scope = course_scope("course_id")
    label, icon, menu, menu_roles = "Course Enrolments", "users", True, MANAGERS
    list_fields = ["course", "student", "completed", "completed_at"]


class ModuleViewSet(CourseContentViewSet):
    queryset = Module.objects.all()
    serializer_class = s.ModuleSerializer
    resource_key = "modules"
    scope = course_scope("course_id")
    label, icon = "Course Modules", "layers"
    list_fields = ["course", "title", "order"]


class LessonViewSet(CourseContentViewSet):
    queryset = Lesson.objects.all()
    serializer_class = s.LessonSerializer
    resource_key = "lessons"
    filterset_fields = ["module", "module__course", "kind", "is_published"]
    scope = course_scope("module__course_id")
    icon = "play"
    list_fields = ["module", "title", "kind", "order", "is_published"]
    ui_actions = [{"name": "complete", "roles": [R.STUDENT], "row": False}]

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        lesson = get_object_or_404(Lesson.objects.select_related("module__course"), pk=pk)
        course = lesson.module.course
        if not is_participant(request.user, course):
            raise PermissionDenied()
        if request.data.get("undo"):
            LessonProgress.objects.filter(lesson=lesson, student=request.user).delete()
        else:
            LessonProgress.objects.get_or_create(lesson=lesson, student=request.user)
        total = Lesson.objects.filter(module__course=course, is_published=True).count()
        done = LessonProgress.objects.filter(student=request.user, lesson__module__course=course).count()
        pct = round(done / total * 100) if total else 0
        if pct >= 100:
            enr, _ = CourseEnrollment.objects.get_or_create(course=course, student=request.user)
            if not enr.completed:
                enr.completed, enr.completed_at = True, timezone.now()
                enr.save()
                if course.issue_certificate:
                    from exams.models import Certificate
                    Certificate.objects.get_or_create(
                        person=request.user, kind="course", title=f"Certificate of completion — {course.title}",
                        defaults={"details": f"has successfully completed the course “{course.title}” "
                                             f"taught by {course.teacher.display_name}."})
                notify(course.teacher, f"{request.user.display_name} completed {course.title}",
                       link=f"/lms/course?id={course.id}")
        return Response({"progress": pct})


# -------------------------------------------------------------- assignments
class AssignmentViewSet(CourseContentViewSet):
    queryset = Assignment.objects.all()
    serializer_class = s.AssignmentSerializer
    resource_key = "assignments"
    scope = course_scope("course_id")
    icon = "clipboard"
    list_fields = ["course", "title", "due_at", "max_marks", "is_published"]
    ui_actions = [{"name": "submit", "roles": [R.STUDENT], "row": False},
                  {"name": "submissions", "roles": MANAGERS, "row": False}]

    def after_save(self, obj, created):
        if created and obj.is_published:
            notify(list(obj.course.student_users()), f"New assignment: {obj.title}",
                   f"Due {timezone.localtime(obj.due_at):%d %b %Y %H:%M}", f"/lms/course?id={obj.course_id}", "assignment")

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def submit(self, request, pk=None):
        a = get_object_or_404(Assignment.objects.select_related("course"), pk=pk)
        if not is_participant(request.user, a.course):
            raise PermissionDenied()
        ser = s.SubmitAssignmentSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        late = timezone.now() > a.due_at
        if late and not a.allow_late:
            raise ValidationError({"detail": "The deadline has passed."})
        sub, _ = Submission.objects.get_or_create(assignment=a, student=request.user)
        if sub.status == Submission.Status.GRADED:
            raise ValidationError({"detail": "Already graded; cannot resubmit."})
        sub.text = ser.validated_data["text"] or sub.text
        if ser.validated_data.get("file"):
            sub.file = ser.validated_data["file"]
        if not sub.text and not sub.file:
            raise ValidationError({"detail": "Add text or attach a file."})
        sub.status = Submission.Status.LATE if late else Submission.Status.SUBMITTED
        sub.save()
        notify(a.course.teacher, f"Submission: {a.title}", f"{request.user.display_name} submitted",
               f"/lms/course?id={a.course_id}")
        return Response({"detail": "Submitted.", "id": sub.id, "status": sub.status})

    @action(detail=True, methods=["get"])
    def submissions(self, request, pk=None):
        a = get_object_or_404(Assignment.objects.select_related("course"), pk=pk)
        if not teaches(request.user, a.course):
            raise PermissionDenied()
        subs = {x.student_id: x for x in a.submissions.select_related("student")}
        rows = []
        for u in a.course.student_users():
            sub = subs.get(u.id)
            rows.append({"student": u.id, "name": u.display_name, "submission": None if not sub else {
                "id": sub.id, "status": sub.status, "text": sub.text, "marks": sub.marks, "feedback": sub.feedback,
                "file": request.build_absolute_uri(sub.file.url) if sub.file else None, "submitted_at": sub.updated_at}})
        return Response({"assignment": {"id": a.id, "title": a.title, "max_marks": a.max_marks, "due_at": a.due_at},
                         "rows": rows})


def submission_scope(qs, user):
    if user.role == R.TEACHER:
        return qs.filter(assignment__course_id__in=visible_course_ids(user) or [])
    if user.role == R.PARENT:
        return qs.filter(student_id__in=children_qs(user).values_list("user_id", flat=True))
    return qs.filter(student=user)


class SubmissionViewSet(LmsBase):
    queryset = Submission.objects.all()
    serializer_class = s.SubmissionSerializer
    resource_key = "submissions"
    write_roles = []
    scope = staticmethod(submission_scope)
    icon = "upload"
    list_fields = ["assignment", "student", "status", "marks", "created_at"]
    ui_actions = [{"name": "grade", "roles": MANAGERS, "row": False}]

    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None):
        sub = get_object_or_404(Submission.objects.select_related("assignment__course"), pk=pk)
        if not teaches(request.user, sub.assignment.course):
            raise PermissionDenied()
        ser = s.GradeSubmissionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        if ser.validated_data["marks"] > sub.assignment.max_marks:
            raise ValidationError({"marks": f"Must be between 0 and {sub.assignment.max_marks}"})
        sub.marks = ser.validated_data["marks"]
        sub.feedback = ser.validated_data["feedback"]
        sub.status = ser.validated_data["status"]
        sub.graded_by, sub.graded_at = request.user, timezone.now()
        sub.save()
        notify(sub.student, f"Assignment graded: {sub.assignment.title}",
               f"Marks: {sub.marks}/{sub.assignment.max_marks}", f"/lms/course?id={sub.assignment.course_id}", "grade")
        return Response({"detail": "Graded."})


# ------------------------------------------------------------------- quizzes
def quiz_is_open(q):
    now = timezone.now()
    return q.is_published and (not q.available_from or q.available_from <= now) and \
        (not q.available_until or q.available_until >= now)


class QuizViewSet(CourseContentViewSet):
    queryset = Quiz.objects.all()
    serializer_class = s.QuizSerializer
    resource_key = "quizzes"
    scope = course_scope("course_id")
    icon = "help"
    list_fields = ["course", "title", "time_limit_minutes", "max_attempts", "is_published"]
    ui_actions = [{"name": "start", "roles": [R.STUDENT], "row": False}]

    @action(detail=True, methods=["post"])
    def start(self, request, pk=None):
        q = get_object_or_404(Quiz.objects.select_related("course"), pk=pk)
        user = request.user
        if not is_participant(user, q.course):
            raise PermissionDenied()
        if not quiz_is_open(q):
            raise ValidationError({"detail": "This quiz is not available now."})
        attempt = QuizAttempt.objects.filter(quiz=q, student=user, status="in_progress").first()
        if attempt and q.time_limit_minutes and timezone.now() > attempt.started_at + timedelta(minutes=q.time_limit_minutes + 1):
            attempt.submitted_at = timezone.now()
            attempt.recompute()
            attempt = None
        if not attempt:
            if QuizAttempt.objects.filter(quiz=q, student=user).count() >= q.max_attempts:
                raise ValidationError({"detail": "No attempts left."})
            attempt = QuizAttempt.objects.create(quiz=q, student=user)
        questions = list(q.questions.prefetch_related("choices"))
        if q.shuffle_questions:
            random.Random(attempt.id).shuffle(questions)
        remaining = None
        if q.time_limit_minutes:
            remaining = max(0, int(q.time_limit_minutes * 60 - (timezone.now() - attempt.started_at).total_seconds()))
        return Response({"attempt": attempt.id,
                         "quiz": {"id": q.id, "title": q.title, "description": q.description,
                                  "time_limit_minutes": q.time_limit_minutes},
                         "remaining_seconds": remaining,
                         "questions": [{"id": qu.id, "text": qu.text, "kind": qu.kind, "marks": qu.marks,
                                        "choices": [{"id": c.id, "text": c.text} for c in qu.choices.all()]}
                                       for qu in questions]})


class QuestionViewSet(CourseContentViewSet):
    queryset = Question.objects.all()
    serializer_class = s.QuestionSerializer
    resource_key = "questions"
    scope = course_scope("quiz__course_id")
    icon = "help"
    list_fields = ["quiz", "text", "kind", "marks", "order"]

    def get_queryset(self):
        qs = super().get_queryset()
        if self.request.user.role in (R.STUDENT, R.PARENT):
            return qs.none()  # students receive questions only through quizzes/start (without answers)
        return qs


class ChoiceViewSet(CourseContentViewSet):
    queryset = Choice.objects.all()
    serializer_class = s.ChoiceSerializer
    resource_key = "choices"
    filterset_fields = ["question", "question__quiz", "is_correct"]
    scope = staticmethod(lambda qs, u: course_scope("question__quiz__course_id")(qs, u) if u.role == R.TEACHER else qs.none())
    icon = "list"
    list_fields = ["question", "text", "is_correct"]


def attempt_scope(qs, user):
    if user.role == R.TEACHER:
        return qs.filter(quiz__course_id__in=visible_course_ids(user) or [])
    if user.role == R.PARENT:
        return qs.filter(student_id__in=children_qs(user).values_list("user_id", flat=True))
    return qs.filter(student=user)


class QuizAttemptViewSet(LmsBase):
    queryset = QuizAttempt.objects.all()
    serializer_class = s.QuizAttemptSerializer
    resource_key = "quiz-attempts"
    write_roles = []
    scope = staticmethod(attempt_scope)
    icon = "check"
    list_fields = ["quiz", "student", "status", "score", "max_score", "passed", "submitted_at"]
    ui_actions = [{"name": "submit", "roles": [R.STUDENT], "row": False},
                  {"name": "review", "roles": ALL, "row": False},
                  {"name": "grade", "roles": MANAGERS, "row": False}]

    @action(detail=True, methods=["post"])
    @transaction.atomic
    def submit(self, request, pk=None):
        attempt = get_object_or_404(QuizAttempt.objects.select_related("quiz"), pk=pk, student=request.user)
        if attempt.status != QuizAttempt.Status.IN_PROGRESS:
            raise ValidationError({"detail": "Already submitted."})
        ser = s.SubmitAttemptSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        given = {a["question"]: a for a in ser.validated_data["answers"]}
        for qu in attempt.quiz.questions.prefetch_related("choices"):
            g = given.get(qu.id, {})
            ans, _ = AttemptAnswer.objects.get_or_create(attempt=attempt, question=qu)
            if qu.kind == Question.Kind.SHORT:
                ans.text_answer, ans.marks_awarded, ans.is_correct = g.get("text", ""), None, None
            else:
                chosen = set(g.get("choices", []))
                ans.selected.set(qu.choices.filter(id__in=chosen))
                correct = set(qu.choices.filter(is_correct=True).values_list("id", flat=True))
                ans.is_correct = bool(chosen) and chosen == correct
                ans.marks_awarded = qu.marks if ans.is_correct else 0
            ans.save()
        attempt.submitted_at = timezone.now()
        attempt.recompute()
        return Response({"detail": "Submitted.", "score": attempt.score, "max_score": attempt.max_score,
                         "status": attempt.status, "passed": attempt.passed})

    @action(detail=True, methods=["get"])
    def review(self, request, pk=None):
        attempt = self.get_object()
        manager = teaches(request.user, attempt.quiz.course)
        show = manager or attempt.quiz.show_answers
        answers = []
        for a in attempt.answers.select_related("question").prefetch_related("selected", "question__choices"):
            answers.append({"answer_id": a.id, "question": a.question.text, "kind": a.question.kind, "marks": a.question.marks,
                            "text_answer": a.text_answer, "selected": [c.id for c in a.selected.all()],
                            "choices": [{"id": c.id, "text": c.text, "is_correct": c.is_correct if show else None}
                                        for c in a.question.choices.all()],
                            "is_correct": a.is_correct, "marks_awarded": a.marks_awarded,
                            "explanation": a.question.explanation if show else ""})
        return Response({"attempt": attempt.id, "student": attempt.student.display_name, "quiz": attempt.quiz.title,
                         "score": attempt.score, "max_score": attempt.max_score, "status": attempt.status,
                         "passed": attempt.passed, "is_manager": manager, "answers": answers})

    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None):
        attempt = self.get_object()
        if not teaches(request.user, attempt.quiz.course):
            raise PermissionDenied()
        ser = s.ManualGradeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        for g in ser.validated_data["answers"]:
            a = get_object_or_404(attempt.answers.select_related("question"), pk=g["answer_id"])
            a.marks_awarded = min(g["marks"], a.question.marks)
            a.is_correct = a.marks_awarded >= a.question.marks
            a.save()
        attempt.recompute()
        notify(attempt.student, f"Quiz graded: {attempt.quiz.title}", f"Score {attempt.score}/{attempt.max_score}")
        return Response({"detail": "Graded.", "score": attempt.score})


# --------------------------------------------------------------- discussions
class DiscussionThreadViewSet(LmsBase):
    queryset = DiscussionThread.objects.all()
    serializer_class = s.DiscussionThreadSerializer
    resource_key = "discussion-threads"
    create_roles = [R.STUDENT]
    scope = course_scope("course_id")
    owner_field, owner_edit = "author", True
    label, icon = "Discussions", "chat"
    list_fields = ["course", "title", "author", "is_pinned", "created_at"]

    def validate_create(self, serializer, extra):
        if not is_participant(self.request.user, serializer.validated_data["course"]):
            raise PermissionDenied()


class DiscussionReplyViewSet(LmsBase):
    queryset = DiscussionReply.objects.all()
    serializer_class = s.DiscussionReplySerializer
    resource_key = "discussion-replies"
    create_roles = [R.STUDENT]
    scope = course_scope("thread__course_id")
    owner_field, owner_edit = "author", True
    icon = "chat"
    list_fields = ["thread", "author", "body", "created_at"]

    def validate_create(self, serializer, extra):
        thread = serializer.validated_data["thread"]
        if thread.is_locked or not is_participant(self.request.user, thread.course):
            raise PermissionDenied("Thread is locked or not accessible.")


class HomeworkViewSet(LmsBase):
    queryset = Homework.objects.all()
    serializer_class = s.HomeworkSerializer
    resource_key = "homework"
    scope = by_section()
    label, icon, menu, menu_roles = "Homework / Diary", "notebook", True, ALL
    list_fields = ["date", "section", "subject", "title", "due_date"]


# ------------------------------------------------------------------ APIViews
class MyCoursesView(APIView):
    def get(self, request):
        user = request.user
        ids = visible_course_ids(user)
        qs = Course.objects.select_related("teacher", "section", "subject")
        if ids is not None:
            qs = qs.filter(id__in=ids)
        out = []
        for c in qs.order_by("title"):
            item = {"id": c.id, "title": c.title, "code": c.code, "teacher": c.teacher.display_name,
                    "section": str(c.section) if c.section else None, "subject": c.subject.name if c.subject else None,
                    "cover": request.build_absolute_uri(c.cover.url) if c.cover else None, "is_published": c.is_published,
                    "lessons": Lesson.objects.filter(module__course=c).count(), "enrollment_type": c.enrollment_type}
            if user.role == R.STUDENT:
                done = LessonProgress.objects.filter(student=user, lesson__module__course=c).count()
                item["progress"] = round(done / item["lessons"] * 100) if item["lessons"] else 0
            out.append(item)
        open_courses = []
        if user.role == R.STUDENT:
            open_courses = [{"id": c.id, "title": c.title, "teacher": c.teacher.display_name}
                            for c in Course.objects.filter(is_published=True, enrollment_type="open")
                            .exclude(enrollments__student=user).select_related("teacher")]
        return Response({"courses": out, "open_courses": open_courses})


class MyTasksView(APIView):
    """Upcoming assignments & quizzes for a student (or a parent's children)."""

    def get(self, request):
        user = request.user
        learners = [user] if user.role == R.STUDENT else [x.user for x in children_qs(user).select_related("user")]
        now = timezone.now()
        items = []
        for learner in learners:
            ids = student_course_ids(learner)
            for a in Assignment.objects.filter(course_id__in=ids, is_published=True,
                                               due_at__gte=now - timedelta(days=7)).select_related("course"):
                sub = Submission.objects.filter(assignment=a, student=learner).first()
                items.append({"type": "assignment", "id": a.id, "title": a.title, "course": a.course.title,
                              "course_id": a.course_id, "due": a.due_at, "student": learner.display_name,
                              "status": sub.status if sub else ("overdue" if a.due_at < now else "pending")})
            for q in Quiz.objects.filter(course_id__in=ids, is_published=True).select_related("course"):
                if q.available_until and q.available_until < now:
                    continue
                done = QuizAttempt.objects.filter(quiz=q, student=learner).exclude(status="in_progress").exists()
                items.append({"type": "quiz", "id": q.id, "title": q.title, "course": q.course.title, "course_id": q.course_id,
                              "due": q.available_until, "status": "done" if done else "pending", "student": learner.display_name})
        items.sort(key=lambda x: (x["due"] is None, x["due"] or now))
        return Response(items)


class ThreadDetailView(APIView):
    def get(self, request, pk):
        t = get_object_or_404(DiscussionThread.objects.select_related("course", "author"), pk=pk)
        if not (teaches(request.user, t.course) or is_participant(request.user, t.course)):
            raise PermissionDenied()
        return Response({"id": t.id, "title": t.title, "body": t.body, "author": t.author.display_name if t.author else "",
                         "created_at": t.created_at, "is_locked": t.is_locked,
                         "replies": [{"id": r.id, "body": r.body, "author": r.author.display_name if r.author else "",
                                      "created_at": r.created_at, "mine": r.author_id == request.user.id}
                                     for r in t.replies.select_related("author")]})


class CourseThreadsView(APIView):
    def get(self, request, course_id):
        c = get_object_or_404(Course, pk=course_id)
        if not (teaches(request.user, c) or is_participant(request.user, c)):
            raise PermissionDenied()
        return Response([{"id": t.id, "title": t.title, "author": t.author.display_name if t.author else "",
                          "is_pinned": t.is_pinned, "replies": t.replies.count(), "created_at": t.created_at}
                         for t in c.threads.select_related("author")])
