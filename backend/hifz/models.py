from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStamped
from people.models import Student

from .quran import JUZ_CHOICES, SURAH_CHOICES

User = settings.AUTH_USER_MODEL


class Quality(models.TextChoices):
    EXCELLENT = "excellent", "Excellent (Mumtaz)"
    GOOD = "good", "Good (Jayyid)"
    AVERAGE = "average", "Average (Maqbool)"
    WEAK = "weak", "Weak (Kamzor)"
    NOT_DONE = "not_done", "Not done / not heard"


class Program(models.TextChoices):
    QAIDA = "qaida", "Noorani Qaida"
    NAZRA = "nazra", "Nazra"
    HIFZ = "hifz", "Hifz"
    MURAJAAH = "murajaah", "Murajaah (Dor / Revision)"
    TAJWEED = "tajweed", "Tajweed"
    TARJUMA = "tarjuma", "Tarjuma-tul-Quran (translation)"


class ParaProgram(models.TextChoices):
    """Programs tracked para-by-para (30 juz)."""

    HIFZ = "hifz", "Hifz (memorisation)"
    NAZRA = "nazra", "Nazra (reading)"
    TARJUMA = "tarjuma", "Tarjuma (translation)"


class HifzRecord(TimeStamped):
    """Daily record of Sabaq (new lesson), Sabqi (recent revision) and Manzil (old revision)."""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="hifz_records")
    date = models.DateField(default=timezone.localdate, db_index=True)
    program = models.CharField(max_length=10, choices=Program.choices, default=Program.HIFZ)
    teacher = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    # Sabaq
    sabaq_surah = models.PositiveSmallIntegerField(choices=SURAH_CHOICES, null=True, blank=True)
    sabaq_from_ayah = models.PositiveSmallIntegerField(null=True, blank=True)
    sabaq_to_ayah = models.PositiveSmallIntegerField(null=True, blank=True)
    sabaq_lines = models.PositiveSmallIntegerField(default=0, help_text="Lines / pages for Qaida & Nazra")
    sabaq_quality = models.CharField(max_length=10, choices=Quality.choices, blank=True)
    # Sabqi
    sabqi_juz = models.PositiveSmallIntegerField(choices=JUZ_CHOICES, null=True, blank=True)
    sabqi_quantity = models.CharField(max_length=60, blank=True, help_text="e.g. 1/4 para, 3 pages")
    sabqi_quality = models.CharField(max_length=10, choices=Quality.choices, blank=True)
    # Manzil
    manzil_juz = models.CharField(max_length=60, blank=True, help_text="e.g. 1-3")
    manzil_quality = models.CharField(max_length=10, choices=Quality.choices, blank=True)
    mistakes = models.PositiveSmallIntegerField(default=0, help_text="Ghalti")
    hesitations = models.PositiveSmallIntegerField(default=0, help_text="Atkan")
    tajweed_rating = models.PositiveSmallIntegerField(default=0, help_text="0-10")
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ("student", "date", "program")

    def __str__(self):
        return f"{self.student} {self.date}"


class JuzProgress(TimeStamped):
    class Status(models.TextChoices):
        NOT_STARTED = "not_started", "Not started"
        IN_PROGRESS = "in_progress", "In progress"
        MEMORIZED = "memorized", "Completed (memorised / read / translated)"
        TESTED = "tested", "Tested & approved"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="juz_progress")
    program = models.CharField(max_length=10, choices=ParaProgram.choices, default=ParaProgram.HIFZ, db_index=True)
    juz = models.PositiveSmallIntegerField(choices=JUZ_CHOICES)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.IN_PROGRESS)
    started_on = models.DateField(null=True, blank=True)
    completed_on = models.DateField(null=True, blank=True)
    tested_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    test_score = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Out of 100")
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["student", "program", "juz"]
        unique_together = ("student", "program", "juz")
        verbose_name_plural = "juz progress"

    def __str__(self):
        return f"{self.student} — {self.get_program_display()} para {self.juz}: {self.get_status_display()}"


# --------------------------------------------------------------------- Qaida
class QaidaLesson(TimeStamped):
    """Catalogue of Noorani Qaida lessons (takhti)."""

    number = models.PositiveSmallIntegerField(unique=True)
    title = models.CharField(max_length=150)
    title_arabic = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["number"]

    def __str__(self):
        return f"Takhti {self.number}: {self.title}"


class QaidaProgress(TimeStamped):
    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        PASSED = "passed", "Passed"
        REPEAT = "repeat", "Needs repetition"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="qaida_progress")
    lesson = models.ForeignKey(QaidaLesson, on_delete=models.CASCADE, related_name="progress")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.IN_PROGRESS)
    started_on = models.DateField(default=timezone.localdate)
    passed_on = models.DateField(null=True, blank=True)
    checked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["student", "lesson__number"]
        unique_together = ("student", "lesson")
        verbose_name_plural = "qaida progress"

    def __str__(self):
        return f"{self.student} — {self.lesson}: {self.get_status_display()}"


# ------------------------------------------------------------------- Tarjuma
class TarjumaProgress(TimeStamped):
    """Surah-wise progress of Tarjuma-tul-Quran (translation & tafseer basics)."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        TESTED = "tested", "Tested & approved"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="tarjuma_progress")
    surah = models.PositiveSmallIntegerField(choices=SURAH_CHOICES)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.IN_PROGRESS)
    ayahs_done = models.PositiveSmallIntegerField(default=0, help_text="Ayahs translated so far (for surahs in progress)")
    started_on = models.DateField(default=timezone.localdate)
    completed_on = models.DateField(null=True, blank=True)
    test_score = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Out of 100")
    tested_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["student", "surah"]
        unique_together = ("student", "surah")
        verbose_name_plural = "tarjuma progress"

    def __str__(self):
        return f"{self.student} — {self.get_surah_display()}: {self.get_status_display()}"


# ---------------------------------------------------------------- Khatm log
class QuranCompletion(TimeStamped):
    """Register of completions: Nazra khatm, Hifz completion, Tarjuma completion, Dor (revision) cycles."""

    class Kind(models.TextChoices):
        NAZRA = "nazra", "Nazra khatm"
        HIFZ = "hifz", "Hifz completion"
        TARJUMA = "tarjuma", "Tarjuma completion"
        DOR = "dor", "Dor / revision cycle"
        QAIDA = "qaida", "Noorani Qaida completion"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="quran_completions")
    kind = models.CharField(max_length=10, choices=Kind.choices)
    number = models.PositiveSmallIntegerField(default=1, help_text="1st, 2nd... khatm of this kind")
    started_on = models.DateField(null=True, blank=True)
    completed_on = models.DateField(default=timezone.localdate)
    remarks = models.CharField(max_length=255, blank=True)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-completed_on"]
        verbose_name = "khatm / completion"
        verbose_name_plural = "khatm register"

    def __str__(self):
        return f"{self.student} — {self.get_kind_display()} #{self.number}"


# -------------------------------------------------------------- Checklists
class ChecklistItem(TimeStamped):
    """Things students learn & get tested on: Tajweed rules, Qira'at, Kalimas, duas, ahadith, Namaz practical."""

    class Category(models.TextChoices):
        TAJWEED = "tajweed", "Tajweed rule"
        QIRAAT = "qiraat", "Qira'at / riwayah"
        KALIMA = "kalima", "Kalimah"
        DUA = "dua", "Masnoon dua"
        HADITH = "hadith", "Hadith"
        SURAH = "surah", "Short surah (memorise)"
        NAMAZ = "namaz", "Namaz & Wudu practical"
        AQAID = "aqaid", "Basic Aqaid / Islamiyat"

    category = models.CharField(max_length=10, choices=Category.choices, db_index=True)
    title = models.CharField(max_length=200)
    arabic = models.TextField(blank=True, help_text="Arabic text (dua / hadith / kalimah)")
    translation = models.TextField(blank=True)
    reference = models.CharField(max_length=200, blank=True, help_text="e.g. Sahih Muslim 1599")
    level = models.CharField(max_length=60, blank=True, help_text="e.g. Qaida, Nazra, Hifz, Grade 1")
    order = models.PositiveIntegerField(default=10)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "order", "title"]

    def __str__(self):
        return f"{self.get_category_display()}: {self.title}"


class StudentChecklist(TimeStamped):
    class Status(models.TextChoices):
        LEARNING = "learning", "Learning"
        LEARNED = "learned", "Learned / memorised"
        TESTED = "tested", "Tested & approved"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="checklist")
    item = models.ForeignKey(ChecklistItem, on_delete=models.CASCADE, related_name="students")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.LEARNING)
    date = models.DateField(default=timezone.localdate)
    score = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Out of 10")
    checked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    remarks = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["student", "item"]
        unique_together = ("student", "item")
        verbose_name_plural = "student checklist"

    def __str__(self):
        return f"{self.student} — {self.item.title}: {self.get_status_display()}"
