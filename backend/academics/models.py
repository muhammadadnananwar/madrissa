from django.conf import settings
from django.db import models

from core.models import TimeStamped

User = settings.AUTH_USER_MODEL


class AcademicYear(TimeStamped):
    name = models.CharField(max_length=50, help_text="e.g. 2026-2027")
    hijri_name = models.CharField(max_length=50, blank=True, help_text="e.g. 1448-1449 AH")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_current:
            AcademicYear.objects.exclude(pk=self.pk).update(is_current=False)

    @classmethod
    def current(cls):
        return cls.objects.filter(is_current=True).first() or cls.objects.first()


class Department(TimeStamped):
    class Kind(models.TextChoices):
        QAIDA = "qaida", "Noorani Qaida"
        NAZRA = "nazra", "Nazra Quran"
        HIFZ = "hifz", "Hifz-ul-Quran"
        TAJWEED = "tajweed", "Tajweed & Qira'at"
        TARJUMA = "tarjuma", "Tarjuma-tul-Quran"
        DARS_E_NIZAMI = "dars_e_nizami", "Dars-e-Nizami (Alim Course)"
        ALIMA = "alima", "Alimah Course (Banaat)"
        TAKHASSUS = "takhassus", "Takhassus (Specialisation)"
        IFTA = "ifta", "Takhassus fil Ifta"
        MODERN = "modern", "Modern / Asri Education"
        SHORT = "short", "Short Courses"
        OTHER = "other", "Other"

    name = models.CharField(max_length=120)
    name_arabic = models.CharField(max_length=120, blank=True)
    code = models.CharField(max_length=20, unique=True)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    head = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="headed_departments")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class ClassLevel(TimeStamped):
    """A grade / darja, e.g. 'Darja Oola', 'Hifz Class', 'Grade 5'."""

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="class_levels")
    name = models.CharField(max_length=100)
    name_arabic = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=1)
    duration_months = models.PositiveIntegerField(default=12)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["department__name", "order"]

    def __str__(self):
        return f"{self.name} — {self.department.code}"


class Room(TimeStamped):
    class Kind(models.TextChoices):
        CLASSROOM = "classroom", "Classroom"
        HALL = "hall", "Hall"
        MASJID = "masjid", "Masjid"
        LAB = "lab", "Computer Lab"
        LIBRARY = "library", "Library"
        OFFICE = "office", "Office"
        OTHER = "other", "Other"

    name = models.CharField(max_length=60)
    building = models.CharField(max_length=60, blank=True)
    capacity = models.PositiveIntegerField(default=30)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.CLASSROOM)

    def __str__(self):
        return f"{self.name} {f'({self.building})' if self.building else ''}".strip()


class Section(TimeStamped):
    class Shift(models.TextChoices):
        MORNING = "morning", "Morning"
        EVENING = "evening", "Evening"
        NIGHT = "night", "Night"
        WEEKEND = "weekend", "Weekend"
        ONLINE = "online", "Online"

    class GenderType(models.TextChoices):
        BANEEN = "male", "Baneen (Boys)"
        BANAAT = "female", "Banaat (Girls)"
        MIXED = "mixed", "Mixed (children)"

    class_level = models.ForeignKey(ClassLevel, on_delete=models.CASCADE, related_name="sections")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="sections")
    name = models.CharField(max_length=40, help_text="e.g. A, B, Halqa 1")
    class_teacher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="class_teacher_of")
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL)
    capacity = models.PositiveIntegerField(default=30)
    gender = models.CharField(max_length=10, choices=GenderType.choices, default=GenderType.BANEEN)
    shift = models.CharField(max_length=10, choices=Shift.choices, default=Shift.MORNING)

    class Meta:
        ordering = ["class_level__department__name", "class_level__order", "name"]

    def __str__(self):
        return f"{self.class_level.name} - {self.name} ({self.academic_year.name})"


class Subject(TimeStamped):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="subjects")
    class_level = models.ForeignKey(ClassLevel, null=True, blank=True, on_delete=models.SET_NULL, related_name="subjects")
    name = models.CharField(max_length=120, help_text="e.g. Fiqh, Hadith, Nahw, Sarf, Mathematics")
    name_arabic = models.CharField(max_length=120, blank=True)
    code = models.CharField(max_length=20)
    book = models.CharField("Kitab / textbook", max_length=200, blank=True, help_text="e.g. Hidayah, Mishkat al-Masabih")
    is_core = models.BooleanField(default=True)
    total_marks = models.PositiveIntegerField(default=100)
    pass_marks = models.PositiveIntegerField(default=40)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["department__name", "name"]

    def __str__(self):
        return f"{self.name}{f' — {self.book}' if self.book else ''}"


class TeacherAssignment(TimeStamped):
    """Which teacher teaches which subject to which section."""

    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="assignments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="assignments")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="teaching_assignments")
    periods_per_week = models.PositiveIntegerField(default=5)

    class Meta:
        unique_together = ("section", "subject", "teacher")

    def __str__(self):
        return f"{self.teacher.display_name}: {self.subject.name} → {self.section}"


class TimeSlot(TimeStamped):
    name = models.CharField(max_length=40, help_text="e.g. Period 1, After Fajr")
    start_time = models.TimeField()
    end_time = models.TimeField()
    order = models.PositiveIntegerField(default=1)
    is_break = models.BooleanField(default=False, help_text="Break / Salah / meal time")

    class Meta:
        ordering = ["order", "start_time"]

    def __str__(self):
        return f"{self.name} ({self.start_time:%H:%M}-{self.end_time:%H:%M})"


class Weekday(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"


class TimetableEntry(TimeStamped):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="timetable")
    day = models.IntegerField(choices=Weekday.choices)
    time_slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL)
    teacher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="timetable_entries")
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL)
    note = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["day", "time_slot__order"]
        unique_together = ("section", "day", "time_slot")
        verbose_name_plural = "timetable entries"

    def __str__(self):
        return f"{self.section} {self.get_day_display()} {self.time_slot.name}"


class Holiday(TimeStamped):
    class Kind(models.TextChoices):
        ISLAMIC = "islamic", "Islamic (Eid, Ashura...)"
        NATIONAL = "national", "National"
        VACATION = "vacation", "Vacation"
        WEEKLY = "weekly", "Weekly off"
        OTHER = "other", "Other"

    title = models.CharField(max_length=120)
    start_date = models.DateField()
    end_date = models.DateField()
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]

    def __str__(self):
        return self.title


class Syllabus(TimeStamped):
    """Planned syllabus / lesson plan with progress tracking."""

    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="syllabus")
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.CASCADE)
    topic = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    planned_date = models.DateField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    completed_on = models.DateField(null=True, blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["subject", "order"]
        verbose_name_plural = "syllabus topics"

    def __str__(self):
        return f"{self.subject.name}: {self.topic}"
