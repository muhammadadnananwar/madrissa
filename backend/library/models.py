from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStamped

User = settings.AUTH_USER_MODEL


class BookCategory(TimeStamped):
    name = models.CharField(max_length=100, help_text="e.g. Tafseer, Hadith, Fiqh, Seerah, Arabic Grammar")
    description = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name_plural = "book categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Book(TimeStamped):
    class Language(models.TextChoices):
        ARABIC = "arabic", "Arabic"
        URDU = "urdu", "Urdu"
        ENGLISH = "english", "English"
        PERSIAN = "persian", "Persian"
        OTHER = "other", "Other"

    title = models.CharField(max_length=250)
    title_arabic = models.CharField(max_length=250, blank=True)
    author = models.CharField(max_length=200, blank=True)
    publisher = models.CharField(max_length=200, blank=True)
    isbn = models.CharField(max_length=30, blank=True)
    category = models.ForeignKey(BookCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="books")
    language = models.CharField(max_length=10, choices=Language.choices, default=Language.ARABIC)
    volumes = models.PositiveIntegerField(default=1)
    edition = models.CharField(max_length=60, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    shelf = models.CharField(max_length=40, blank=True, help_text="Rack / shelf location")
    total_copies = models.PositiveIntegerField(default=1)
    available_copies = models.PositiveIntegerField(default=1)
    cover = models.ImageField(upload_to="library/covers/", null=True, blank=True)
    pdf = models.FileField("E-book (PDF)", upload_to="library/ebooks/", null=True, blank=True)
    is_reference_only = models.BooleanField(default=False, help_text="Cannot be issued (read in library)")
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title}{f' — {self.author}' if self.author else ''}"


def default_due():
    return timezone.localdate() + timedelta(days=14)


class BookIssue(TimeStamped):
    class Status(models.TextChoices):
        ISSUED = "issued", "Issued"
        RETURNED = "returned", "Returned"
        LOST = "lost", "Lost"

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="issues")
    borrower = models.ForeignKey(User, on_delete=models.CASCADE, related_name="book_issues")
    issued_on = models.DateField(default=timezone.localdate)
    due_date = models.DateField(default=default_due)
    returned_on = models.DateField(null=True, blank=True, editable=False)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ISSUED, db_index=True)
    fine = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    fine_paid = models.BooleanField(default=False)
    remarks = models.CharField(max_length=200, blank=True)
    issued_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-issued_on"]

    def __str__(self):
        return f"{self.book.title} → {self.borrower.display_name}"

    @property
    def is_overdue(self):
        return self.status == self.Status.ISSUED and self.due_date < timezone.localdate()


class BookReservation(TimeStamped):
    class Status(models.TextChoices):
        WAITING = "waiting", "Waiting"
        FULFILLED = "fulfilled", "Fulfilled"
        CANCELLED = "cancelled", "Cancelled"

    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reservations")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="book_reservations")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.WAITING)

    def __str__(self):
        return f"{self.user.display_name} reserved {self.book.title}"
