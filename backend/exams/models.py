import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from academics.models import AcademicYear, Room, Section, Subject
from core.models import TimeStamped
from people.models import Student

User = settings.AUTH_USER_MODEL


class GradeScale(TimeStamped):
    """e.g. Wifaq-ul-Madaris grading: Mumtaz, Jayyid Jiddan, Jayyid, Maqbool, Rasib."""

    name = models.CharField(max_length=40, help_text="e.g. Mumtaz (Distinction)")
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    max_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    grade_point = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    is_pass = models.BooleanField(default=True)
    remarks = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ["-min_percentage"]

    def __str__(self):
        return f"{self.name} ({self.min_percentage}-{self.max_percentage}%)"

    @classmethod
    def for_percentage(cls, pct):
        return cls.objects.filter(min_percentage__lte=pct, max_percentage__gte=pct).first()


class Exam(TimeStamped):
    class Kind(models.TextChoices):
        MONTHLY = "monthly", "Monthly test"
        QUARTERLY = "quarterly", "Quarterly (Sehmahi)"
        HALF_YEARLY = "half_yearly", "Half-yearly (Shashmahi)"
        ANNUAL = "annual", "Annual (Salana)"
        BOARD = "board", "Board exam (Wifaq / Tanzeem)"
        ENTRY = "entry", "Entry test"
        HIFZ = "hifz", "Hifz assessment"

    name = models.CharField(max_length=150)
    kind = models.CharField(max_length=15, choices=Kind.choices, default=Kind.MONTHLY)
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="exams")
    start_date = models.DateField()
    end_date = models.DateField()
    weightage = models.PositiveIntegerField(default=100, help_text="% weight in final result")
    is_published = models.BooleanField(default=False, help_text="Results visible to students & parents")
    instructions = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.name} ({self.academic_year})"


class ExamPaper(TimeStamped):
    """A scheduled paper of an exam (date sheet row)."""

    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="papers")
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="exam_papers")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL)
    max_marks = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    pass_marks = models.DecimalField(max_digits=6, decimal_places=2, default=40)
    examiner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="examined_papers")
    invigilator = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="invigilated_papers")
    marks_locked = models.BooleanField(default=False)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ("exam", "section", "subject")

    def __str__(self):
        return f"{self.exam.name}: {self.subject.name} — {self.section}"


class Mark(TimeStamped):
    paper = models.ForeignKey(ExamPaper, on_delete=models.CASCADE, related_name="marks")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="marks")
    marks_obtained = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    is_absent = models.BooleanField(default=False)
    remarks = models.CharField(max_length=200, blank=True)
    entered_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        unique_together = ("paper", "student")

    def __str__(self):
        return f"{self.student} {self.paper.subject.name}: {self.marks_obtained}"


def _serial():
    return f"SND-{timezone.now():%Y}-{secrets.token_hex(3).upper()}"


def _verify_code():
    return secrets.token_urlsafe(9)


class Certificate(TimeStamped):
    class Kind(models.TextChoices):
        HIFZ = "hifz", "Hifz-ul-Quran Sanad"
        NAZRA = "nazra", "Nazra completion"
        ALIM = "alim", "Shahadat-ul-Alamiyyah (Alim)"
        TAJWEED = "tajweed", "Tajweed / Qira'at Sanad"
        TARJUMA = "tarjuma", "Tarjuma-tul-Quran completion"
        QAIDA = "qaida", "Noorani Qaida completion"
        COURSE = "course", "Course completion"
        CHARACTER = "character", "Character certificate"
        LEAVING = "leaving", "School leaving certificate"
        EXPERIENCE = "experience", "Experience certificate (staff)"
        ACHIEVEMENT = "achievement", "Achievement / Merit"

    person = models.ForeignKey(User, on_delete=models.CASCADE, related_name="certificates")
    kind = models.CharField(max_length=15, choices=Kind.choices)
    title = models.CharField(max_length=200)
    serial_no = models.CharField(max_length=40, unique=True, default=_serial)
    verification_code = models.CharField(max_length=30, unique=True, default=_verify_code, editable=False)
    issue_date = models.DateField(default=timezone.localdate)
    details = models.TextField(blank=True, help_text="Body text printed on certificate")
    grade = models.CharField(max_length=40, blank=True)
    is_revoked = models.BooleanField(default=False)
    issued_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.serial_no} — {self.title}"
