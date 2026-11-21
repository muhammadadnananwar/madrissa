from django.conf import settings
from django.db import models
from django.utils import timezone

from academics.models import Department
from core.models import TimeStamped

User = settings.AUTH_USER_MODEL


class SiteSettings(TimeStamped):
    """Singleton with institution-wide settings used by the website and the portal."""

    name = models.CharField(max_length=200, default="Jamia Darul Uloom")
    name_arabic = models.CharField(max_length=200, blank=True, default="الجامعة دار العلوم")
    tagline = models.CharField(max_length=255, blank=True, default="Preserving the Quran, nurturing scholars")
    logo = models.ImageField(upload_to="site/", null=True, blank=True)
    founded_year = models.PositiveIntegerField(null=True, blank=True)
    affiliation = models.CharField(max_length=200, blank=True, help_text="e.g. Wifaq-ul-Madaris Al-Arabia Pakistan")
    registration_no = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    phone = models.CharField(max_length=60, blank=True)
    whatsapp = models.CharField(max_length=60, blank=True)
    email = models.EmailField(blank=True)
    map_embed_url = models.URLField(max_length=600, blank=True)
    facebook = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    about_short = models.TextField(blank=True)
    donation_bank_details = models.TextField(blank=True, help_text="Bank / JazzCash / Easypaisa details shown on donate page")
    admissions_open = models.BooleanField(default=True)
    # Portal-wide settings
    currency = models.CharField(max_length=10, default="PKR")
    library_fine_per_day = models.DecimalField(max_digits=8, decimal_places=2, default=10)
    late_fee_per_invoice = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    attendance_late_after_minutes = models.PositiveIntegerField(default=15)
    min_attendance_percent = models.PositiveIntegerField(default=75)
    working_days = models.JSONField(default=list, blank=True, help_text="Weekday numbers 0=Mon..6=Sun; empty = Mon-Sat")
    notify_guardian_on_absence = models.BooleanField(default=True)
    prayer_city = models.CharField(max_length=60, default="Karachi")
    prayer_country = models.CharField(max_length=60, default="Pakistan")

    class Meta:
        verbose_name_plural = "site settings"

    def __str__(self):
        return self.name

    @classmethod
    def get(cls):
        obj = cls.objects.first()
        return obj or cls.objects.create()

    def working_weekdays(self):
        return self.working_days or [0, 1, 2, 3, 4, 5]


class Page(TimeStamped):
    """Static content pages: history, background, vision, aims, rules, founder's message..."""

    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=255, blank=True)
    body = models.TextField(help_text="HTML or plain text")
    image = models.ImageField(upload_to="pages/", null=True, blank=True)
    order = models.PositiveIntegerField(default=10)
    show_in_menu = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Slide(TimeStamped):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to="slides/", null=True, blank=True)
    cta_text = models.CharField(max_length=60, blank=True)
    cta_link = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class Program(TimeStamped):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    title_arabic = models.CharField(max_length=200, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    summary = models.CharField(max_length=300)
    description = models.TextField(blank=True)
    duration = models.CharField(max_length=60, blank=True)
    eligibility = models.CharField(max_length=255, blank=True)
    timings = models.CharField(max_length=120, blank=True)
    image = models.ImageField(upload_to="programs/", null=True, blank=True)
    icon = models.CharField(max_length=30, default="book")
    order = models.PositiveIntegerField(default=10)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.title


class NewsPost(TimeStamped):
    slug = models.SlugField(max_length=220, unique=True)
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=300, blank=True)
    body = models.TextField()
    image = models.ImageField(upload_to="news/", null=True, blank=True)
    category = models.CharField(max_length=60, blank=True)
    published_at = models.DateTimeField(default=timezone.now)
    is_published = models.BooleanField(default=True)
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class GalleryAlbum(TimeStamped):
    title = models.CharField(max_length=200)
    description = models.CharField(max_length=300, blank=True)
    cover = models.ImageField(upload_to="gallery/covers/", null=True, blank=True)
    date = models.DateField(default=timezone.localdate)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.title


class GalleryImage(TimeStamped):
    album = models.ForeignKey(GalleryAlbum, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=200, blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.caption or f"Image {self.pk}"


class Testimonial(TimeStamped):
    name = models.CharField(max_length=150)
    role = models.CharField(max_length=150, blank=True, help_text="e.g. Parent, Alumnus 2015")
    quote = models.TextField()
    photo = models.ImageField(upload_to="testimonials/", null=True, blank=True)
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class FAQ(TimeStamped):
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=60, default="General")
    order = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["category", "order"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class BoardMember(TimeStamped):
    """Founders, trustees, Majlis-e-Shura and patrons."""

    name = models.CharField(max_length=150)
    title = models.CharField(max_length=150, help_text="e.g. Founder, Patron-in-chief, Member Shura")
    photo = models.ImageField(upload_to="board/", null=True, blank=True)
    bio = models.TextField(blank=True)
    is_founder = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Stat(TimeStamped):
    label = models.CharField(max_length=100, help_text="e.g. Huffaz graduated")
    value = models.CharField(max_length=30)
    icon = models.CharField(max_length=30, blank=True)
    order = models.PositiveIntegerField(default=10)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.value} {self.label}"


class Download(TimeStamped):
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to="downloads/")
    category = models.CharField(max_length=60, default="General", help_text="Prospectus, Forms, Syllabus...")
    is_published = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class ContactMessage(TimeStamped):
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    subject = models.CharField(max_length=200)
    department = models.CharField(max_length=150, blank=True)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    reply_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name}: {self.subject}"


class Subscriber(TimeStamped):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email


class FatwaQuestion(TimeStamped):
    """Dar-ul-Ifta: questions from the public answered by the Muftis."""

    class Status(models.TextChoices):
        NEW = "new", "New"
        ASSIGNED = "assigned", "Assigned"
        ANSWERED = "answered", "Answered"
        REJECTED = "rejected", "Not answerable / duplicate"

    fatwa_no = models.CharField(max_length=30, blank=True)
    name = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    city = models.CharField(max_length=80, blank=True)
    category = models.CharField(max_length=60, default="General", help_text="Taharah, Salah, Zakat, Nikah, Muamalat...")
    title = models.CharField(max_length=200)
    question = models.TextField()
    answer = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.NEW, db_index=True)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="fatwas")
    answered_at = models.DateTimeField(null=True, blank=True, editable=False)
    is_public = models.BooleanField(default=True, help_text="Publish answer on the website (asker's name hidden)")

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
