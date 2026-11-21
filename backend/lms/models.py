from django.conf import settings
from django.db import models
from django.utils import timezone

from academics.models import Section, Subject
from core.models import TimeStamped

User = settings.AUTH_USER_MODEL


class Course(TimeStamped):
    class Enrollment(models.TextChoices):
        SECTION = "section", "Automatic (students of the section)"
        OPEN = "open", "Open (self enrolment)"
        MANUAL = "manual", "Manual (teacher/admin enrols)"

    title = models.CharField(max_length=200)
    code = models.CharField(max_length=30, blank=True)
    description = models.TextField(blank=True)
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL)
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL, related_name="courses")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="courses_taught")
    co_teachers = models.ManyToManyField(User, blank=True, related_name="courses_co_taught")
    cover = models.ImageField(upload_to="lms/covers/", null=True, blank=True)
    enrollment_type = models.CharField(max_length=10, choices=Enrollment.choices, default=Enrollment.SECTION)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_published = models.BooleanField(default=True)
    issue_certificate = models.BooleanField(default=False, help_text="Issue a certificate on 100% completion")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def student_users(self):
        from accounts.models import User as U
        ids = set(self.enrollments.values_list("student_id", flat=True))
        if self.enrollment_type == self.Enrollment.SECTION and self.section_id:
            ids |= set(self.section.students.filter(status="active").values_list("user_id", flat=True))
        return U.objects.filter(id__in=ids)


class CourseEnrollment(TimeStamped):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="course_enrollments")
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("course", "student")

    def __str__(self):
        return f"{self.student.display_name} → {self.course}"


class Module(TimeStamped):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["course", "order"]

    def __str__(self):
        return f"{self.course.title} / {self.title}"


class Lesson(TimeStamped):
    class Kind(models.TextChoices):
        TEXT = "text", "Text / Notes"
        VIDEO = "video", "Video (YouTube / URL)"
        AUDIO = "audio", "Audio (recitation, lecture)"
        PDF = "pdf", "PDF / Document"
        LINK = "link", "External link"

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.TEXT)
    content = models.TextField(blank=True, help_text="Lesson text (Markdown/HTML allowed)")
    media_url = models.URLField(blank=True, help_text="YouTube / audio / external link")
    file = models.FileField(upload_to="lms/lessons/", null=True, blank=True)
    duration_minutes = models.PositiveIntegerField(default=0)
    order = models.PositiveIntegerField(default=1)
    is_published = models.BooleanField(default=True)
    release_at = models.DateTimeField(null=True, blank=True, help_text="Drip content: visible from this time")

    class Meta:
        ordering = ["module__order", "order"]

    def __str__(self):
        return self.title


class LessonProgress(TimeStamped):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name="progress")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="lesson_progress")
    completed = models.BooleanField(default=True)
    completed_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ("lesson", "student")
        verbose_name_plural = "lesson progress"


class Assignment(TimeStamped):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=200)
    instructions = models.TextField()
    attachment = models.FileField(upload_to="lms/assignments/", null=True, blank=True)
    due_at = models.DateTimeField()
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=10)
    allow_late = models.BooleanField(default=True)
    is_published = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-due_at"]

    def __str__(self):
        return self.title


class Submission(TimeStamped):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        LATE = "late", "Submitted late"
        GRADED = "graded", "Graded"
        RETURNED = "returned", "Returned for resubmission"

    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    text = models.TextField(blank=True)
    file = models.FileField(upload_to="lms/submissions/", null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SUBMITTED)
    marks = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+", editable=False)
    graded_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("assignment", "student")

    def __str__(self):
        return f"{self.student.display_name} — {self.assignment}"


class Quiz(TimeStamped):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="quizzes")
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    time_limit_minutes = models.PositiveIntegerField(default=0, help_text="0 = no limit")
    max_attempts = models.PositiveIntegerField(default=1)
    pass_percentage = models.PositiveIntegerField(default=50)
    shuffle_questions = models.BooleanField(default=False)
    show_answers = models.BooleanField(default=True, help_text="Show correct answers after submission")
    available_from = models.DateTimeField(null=True, blank=True)
    available_until = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "quizzes"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Question(TimeStamped):
    class Kind(models.TextChoices):
        MCQ = "mcq", "Multiple choice (one answer)"
        MULTI = "multi", "Multiple choice (many answers)"
        TRUE_FALSE = "true_false", "True / False"
        SHORT = "short", "Short answer (manual grading)"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    kind = models.CharField(max_length=12, choices=Kind.choices, default=Kind.MCQ)
    marks = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    order = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True)

    class Meta:
        ordering = ["quiz", "order"]

    def __str__(self):
        return self.text[:80]


class Choice(TimeStamped):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="choices")
    text = models.CharField(max_length=300)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return self.text


class QuizAttempt(TimeStamped):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        SUBMITTED = "submitted", "Submitted (awaiting grading)"
        GRADED = "graded", "Graded"

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="quiz_attempts")
    started_at = models.DateTimeField(default=timezone.now)
    submitted_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.IN_PROGRESS)
    score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    max_score = models.DecimalField(max_digits=7, decimal_places=2, default=0)
    passed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.student.display_name} — {self.quiz}"

    def recompute(self):
        answers = list(self.answers.select_related("question"))
        self.score = sum((a.marks_awarded or 0) for a in answers)
        self.max_score = sum(q.marks for q in self.quiz.questions.all())
        pending = any(a.question.kind == Question.Kind.SHORT and a.marks_awarded is None for a in answers)
        self.status = self.Status.SUBMITTED if pending else self.Status.GRADED
        pct = (self.score / self.max_score * 100) if self.max_score else 0
        self.passed = pct >= self.quiz.pass_percentage
        self.save()


class AttemptAnswer(TimeStamped):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected = models.ManyToManyField(Choice, blank=True)
    text_answer = models.TextField(blank=True)
    is_correct = models.BooleanField(null=True)
    marks_awarded = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ("attempt", "question")


class DiscussionThread(TimeStamped):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="threads")
    title = models.CharField(max_length=200)
    body = models.TextField()
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self):
        return self.title


class DiscussionReply(TimeStamped):
    thread = models.ForeignKey(DiscussionThread, on_delete=models.CASCADE, related_name="replies")
    body = models.TextField()
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["created_at"]
        verbose_name_plural = "discussion replies"

    def __str__(self):
        return self.body[:60]


class Homework(TimeStamped):
    """Daily diary / homework visible to students and parents."""

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="homework")
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL)
    date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    attachment = models.FileField(upload_to="lms/homework/", null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "homework / diary"

    def __str__(self):
        return f"{self.section}: {self.title}"
