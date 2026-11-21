"""
Content of the public website (the React site in /website).

The shapes mirror what the website's pages read, so the public API in ``cms/api.py`` is a thin
translation (snake_case -> camelCase). Everything is edited from the portal under "Website".
Images can either be uploaded or given as a URL (``*_url``); an uploaded file wins.
"""
from django.db import models
from django.utils import timezone
from django.utils.text import slugify

from core.models import TimeStamped

PLACEHOLDER_HELP = "Tick for sample text that still has to be replaced (shows a 'Sample' badge on the website)"


def unique_slug(instance, source, field="slug"):
    if getattr(instance, field):
        return getattr(instance, field)
    base = slugify(source)[:200] or "item"
    slug, n = base, 2
    model = type(instance)
    while model.objects.filter(**{field: slug}).exclude(pk=instance.pk).exists():
        slug, n = f"{base}-{n}", n + 1
    return slug


def _default_hero():
    return {"title": "Shape Your Future With Excellence", "subtitle": "", "image": "",
            "primaryCta": {"label": "Apply Now", "link": "/admissions/apply"},
            "secondaryCta": {"label": "Explore Programs", "link": "/academics"}}


def _default_banner():
    return {"enabled": False, "text": "", "link": "/admissions"}


def _default_about():
    return {"intro": "", "history": "", "vision": "", "mission": "", "image": "",
            "coreValues": [], "achievements": [], "accreditations": []}


def _default_person():
    return {"name": "", "title": "", "message": "", "photo": ""}


def _default_admissions():
    return {"intro": "", "schedule": [], "generalRequirements": [], "prospectusUrl": "", "feeNote": ""}


def _default_contact():
    return {"address": "", "city": "", "phones": [], "emails": [], "officeHours": "", "mapQuery": ""}


def _default_social():
    return {"facebook": "", "instagram": "", "twitter": "", "youtube": "", "linkedin": ""}


def _default_seo():
    return {"defaultTitle": "University of Muhammadia Saifia (UMS)", "defaultDescription": ""}


LIST_HELP = 'List of {"title", "description", "icon", "image"} — icon names: BookOpen, GraduationCap, Users, Landmark, ...'


class WebsiteSettings(TimeStamped):
    """Singleton with all site-wide editable content of the public website."""
    university_name = models.CharField(max_length=200, default="University of Muhammadia Saifia")
    university_name_ur = models.CharField("University name (Urdu)", max_length=200, blank=True)
    short_name = models.CharField(max_length=20, default="UMS")
    tagline = models.CharField(max_length=255, blank=True)
    tagline_ur = models.CharField("Tagline (Urdu)", max_length=255, blank=True)
    hero = models.JSONField(default=_default_hero, help_text="title, subtitle, image (URL), primaryCta {label, link}, secondaryCta {label, link}")
    hero_image = models.ImageField(upload_to="website/", null=True, blank=True, help_text="Upload to replace hero.image")
    admission_banner = models.JSONField(default=_default_banner, help_text="enabled, text, link — the gold strip above the menu")
    admissions_open = models.BooleanField(default=True, help_text="Accept online applications")
    current_session = models.CharField(max_length=60, blank=True, help_text="e.g. 2026–2027")
    stats = models.JSONField(default=list, blank=True, help_text='List of {"label", "value"}')
    about = models.JSONField(default=_default_about, help_text="intro, history, vision, mission, image, coreValues[], achievements[], accreditations[]")
    about_image = models.ImageField(upload_to="website/", null=True, blank=True, help_text="Upload to replace about.image")
    vice_chancellor = models.JSONField("Head's message", default=_default_person, help_text="name, title, message, photo")
    vice_chancellor_photo = models.ImageField(upload_to="website/", null=True, blank=True)
    chancellor = models.JSONField(default=_default_person, blank=True, help_text="name, title, message, photo")
    leadership = models.JSONField(default=list, blank=True, help_text='List of {"name", "designation", "photo", "bio"}')
    why_choose = models.JSONField(default=list, blank=True, help_text=LIST_HELP)
    campus_facilities = models.JSONField(default=list, blank=True, help_text=LIST_HELP)
    societies = models.JSONField(default=list, blank=True, help_text=LIST_HELP)
    admissions = models.JSONField(default=_default_admissions, help_text="intro, schedule[{step, date, note}], generalRequirements[], prospectusUrl, feeNote")
    contact = models.JSONField(default=_default_contact, help_text="address, city, phones[], emails[], officeHours, mapQuery")
    social = models.JSONField(default=_default_social, blank=True, help_text="facebook, instagram, twitter, youtube, linkedin (full URLs)")
    whatsapp_number = models.CharField(max_length=20, blank=True, help_text="International format without + e.g. 923001234567")
    seo = models.JSONField(default=_default_seo, help_text="defaultTitle, defaultDescription")
    footer_text = models.TextField(blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "Website settings"

    def __str__(self):
        return self.university_name

    @classmethod
    def load(cls):
        obj = cls.objects.first()
        return obj or cls.objects.create()


class Department(TimeStamped):
    name = models.CharField(max_length=150)
    name_ur = models.CharField("Name (Urdu)", max_length=150, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    code = models.CharField(max_length=12, blank=True)
    faculty = models.CharField("Faculty / school", max_length=120, blank=True, help_text="Grouping, e.g. Islamic Sciences")
    short_description = models.CharField(max_length=400, blank=True)
    short_description_ur = models.CharField("Short description (Urdu)", max_length=400, blank=True)
    introduction = models.TextField(blank=True, help_text="Paragraphs separated by blank lines; '## ' starts a heading, '- ' a bullet")
    head_name = models.CharField(max_length=150, blank=True)
    head_designation = models.CharField(max_length=150, blank=True)
    head_message = models.TextField(blank=True)
    image = models.ImageField(upload_to="website/departments/", null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=40, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_placeholder = models.BooleanField(default=False, help_text=PLACEHOLDER_HELP)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)


class Program(TimeStamped):
    class Level(models.TextChoices):
        QURAN = "quran", "Quran Studies"
        DARS_NIZAMI = "dars_nizami", "Dars-e-Nizami"
        SPECIALIZATION = "specialization", "Takhassus (Specialisation)"
        SHORT_COURSE = "short_course", "Short Course"
        UNDERGRADUATE = "undergraduate", "Undergraduate"
        GRADUATE = "graduate", "Graduate"
        POSTGRADUATE = "postgraduate", "Postgraduate"
        DIPLOMA = "diploma", "Diploma"
        CERTIFICATE = "certificate", "Certificate"

    class Mode(models.TextChoices):
        ON_CAMPUS = "on_campus", "On campus"
        ONLINE = "online", "Online"
        BOTH = "both", "On campus & online"

    class Shift(models.TextChoices):
        MORNING = "morning", "Morning"
        EVENING = "evening", "Evening"
        WEEKEND = "weekend", "Weekend"
        BOTH = "both", "Morning & evening"

    title = models.CharField(max_length=200)
    title_ur = models.CharField("Title (Urdu)", max_length=200, blank=True)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    code = models.CharField(max_length=20, blank=True)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.QURAN)
    delivery_mode = models.CharField(max_length=12, choices=Mode.choices, default=Mode.ON_CAMPUS)
    audience = models.CharField(max_length=80, blank=True, help_text="e.g. Men & Women")
    class_days = models.CharField(max_length=80, blank=True, help_text="e.g. Saturday & Sunday only")
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="programs")
    duration = models.CharField(max_length=60, blank=True)
    semesters = models.PositiveIntegerField(null=True, blank=True)
    total_credit_hours = models.PositiveIntegerField(null=True, blank=True)
    shift = models.CharField(max_length=10, choices=Shift.choices, default=Shift.MORNING)
    short_description = models.CharField(max_length=500, blank=True)
    overview = models.TextField(blank=True, help_text="Paragraphs separated by blank lines; '## ' heading, '- ' bullet")
    eligibility = models.JSONField(default=list, blank=True, help_text="List of lines")
    admission_requirements = models.JSONField(default=list, blank=True, help_text="List of lines")
    career_prospects = models.JSONField(default=list, blank=True, help_text="List of lines")
    fee = models.JSONField(default=dict, blank=True, help_text="admissionFee, tuitionPerSemester, otherCharges, currency, note")
    seats = models.PositiveIntegerField(null=True, blank=True)
    minimum_percentage = models.PositiveIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to="website/programs/", null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    is_featured = models.BooleanField(default=False, help_text="Show on the homepage")
    is_admission_open = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_placeholder = models.BooleanField(default=False, help_text=PLACEHOLDER_HELP)

    class Meta:
        ordering = ["level", "title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)


class Faculty(TimeStamped):
    """Public profile of a teacher (Ustadh) shown on the website."""
    name = models.CharField(max_length=150)
    name_ur = models.CharField("Name (Urdu)", max_length=150, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    designation = models.CharField(max_length=150)
    designation_ur = models.CharField("Designation (Urdu)", max_length=200, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="faculty_members")
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True, help_text="Private — never shown on the website")
    qualifications = models.JSONField(default=list, blank=True, help_text='List of {"degree", "institution", "year"}')
    specialization = models.CharField(max_length=200, blank=True)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="website/faculty/", null=True, blank=True)
    photo_url = models.URLField(max_length=500, blank=True)
    research_interests = models.JSONField(default=list, blank=True)
    publications = models.JSONField(default=list, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_placeholder = models.BooleanField(default=False, help_text=PLACEHOLDER_HELP)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "Faculty"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.slug = unique_slug(self, self.name)
        super().save(*args, **kwargs)


class News(TimeStamped):
    class Category(models.TextChoices):
        NEWS = "news", "News"
        ACHIEVEMENT = "achievement", "Achievement"
        RESEARCH = "research", "Research"
        CAMPUS = "campus", "Campus"
        PRESS = "press", "Press release"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    excerpt = models.CharField(max_length=400, blank=True)
    content = models.TextField(help_text="Paragraphs separated by blank lines; '## ' heading, '- ' bullet")
    cover_image = models.ImageField(upload_to="website/news/", null=True, blank=True)
    cover_image_url = models.URLField(max_length=500, blank=True)
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.NEWS)
    tags = models.JSONField(default=list, blank=True)
    is_published = models.BooleanField(default=True)
    published_at = models.DateTimeField(default=timezone.now)
    is_placeholder = models.BooleanField(default=False, help_text=PLACEHOLDER_HELP)

    class Meta:
        ordering = ["-published_at"]
        verbose_name_plural = "News"

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)


class Announcement(TimeStamped):
    """Public announcements / notices (the homepage ticker and News & Events > Announcements)."""
    class Type(models.TextChoices):
        GENERAL = "general", "General"
        ADMISSION = "admission", "Admission"
        EXAMINATION = "examination", "Examination"
        ACADEMIC = "academic", "Academic"
        ADMINISTRATIVE = "administrative", "Administrative"

    title = models.CharField(max_length=300)
    content = models.TextField(blank=True)
    type = models.CharField(max_length=15, choices=Type.choices, default=Type.GENERAL)
    attachment = models.FileField(upload_to="website/announcements/", null=True, blank=True)
    link = models.CharField(max_length=300, blank=True, help_text="Site path like /admissions/apply or a full URL")
    is_pinned = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    publish_date = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-is_pinned", "-publish_date"]

    def __str__(self):
        return self.title


class CalendarItem(TimeStamped):
    class Category(models.TextChoices):
        ACADEMIC = "academic", "Academic"
        EXAMINATION = "examination", "Examination"
        HOLIDAY = "holiday", "Holiday"
        ADMISSION = "admission", "Admission"
        EVENT = "event", "Event"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.ACADEMIC)
    term = models.CharField(max_length=60, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["start_date"]
        verbose_name = "Academic calendar item"

    def __str__(self):
        return self.title


class GalleryItem(TimeStamped):
    class Category(models.TextChoices):
        CAMPUS = "campus", "Campus"
        LIBRARY = "library", "Library"
        LABS = "labs", "Labs / classrooms"
        SPORTS = "sports", "Sports"
        EVENTS = "events", "Events"
        STUDENTS = "students", "Students"
        OTHER = "other", "Other"

    title = models.CharField(max_length=200)
    image = models.ImageField(upload_to="website/gallery/", null=True, blank=True)
    image_url = models.URLField(max_length=500, blank=True)
    category = models.CharField(max_length=10, choices=Category.choices, default=Category.CAMPUS)
    description = models.CharField(max_length=300, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="gallery_items")
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return self.title


class Document(TimeStamped):
    """Download Center (prospectus, forms, notices...)."""
    class Category(models.TextChoices):
        PROSPECTUS = "prospectus", "Prospectus"
        NOTICE = "notice", "Notice"
        EXAMINATION = "examination", "Examination"
        FORM = "form", "Form"
        POLICY = "policy", "Policy"
        TIMETABLE = "timetable", "Timetable"
        OTHER = "other", "Other"

    title = models.CharField(max_length=200)
    description = models.CharField(max_length=400, blank=True)
    category = models.CharField(max_length=12, choices=Category.choices, default=Category.NOTICE)
    file = models.FileField(upload_to="website/documents/", null=True, blank=True)
    file_url = models.URLField(max_length=500, blank=True, help_text="Use instead of uploading a file")
    audience = models.CharField(max_length=10, choices=[("public", "Public"), ("students", "Students only")], default="public")
    downloads = models.PositiveIntegerField(default=0, editable=False)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "title"]

    def __str__(self):
        return self.title


class MeritList(TimeStamped):
    title = models.CharField(max_length=200)
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name="merit_lists")
    session = models.CharField(max_length=60, blank=True)
    round = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)


class MeritListEntry(TimeStamped):
    merit_list = models.ForeignKey(MeritList, on_delete=models.CASCADE, related_name="entries")
    application = models.ForeignKey("people.AdmissionApplication", null=True, blank=True, on_delete=models.SET_NULL, related_name="merit_entries")
    application_number = models.CharField(max_length=40)
    name = models.CharField(max_length=150)
    aggregate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    rank = models.PositiveIntegerField()

    class Meta:
        ordering = ["merit_list", "rank"]
        verbose_name_plural = "Merit list entries"

    def __str__(self):
        return f"#{self.rank} {self.name}"


class Testimonial(TimeStamped):
    name = models.CharField(max_length=150)
    program = models.CharField(max_length=150, blank=True)
    batch = models.CharField(max_length=60, blank=True)
    quote = models.TextField(max_length=600)
    photo = models.ImageField(upload_to="website/testimonials/", null=True, blank=True)
    photo_url = models.URLField(max_length=500, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    is_placeholder = models.BooleanField(default=False, help_text=PLACEHOLDER_HELP)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return self.name


class Faq(TimeStamped):
    class Category(models.TextChoices):
        GENERAL = "general", "General"
        ADMISSION = "admission", "Admission"
        ACADEMICS = "academics", "Academics"
        FEES = "fees", "Fees"
        STUDENT_PORTAL = "student_portal", "Student portal"

    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=15, choices=Category.choices, default=Category.GENERAL)
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["category", "order"]
        verbose_name = "FAQ"

    def __str__(self):
        return self.question


class Page(TimeStamped):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True, help_text="URL: /pages/<slug>")
    summary = models.CharField(max_length=400, blank=True)
    content = models.TextField(help_text="Paragraphs separated by blank lines; '## ' heading, '- ' bullet, '1. ' numbered")
    meta_description = models.CharField(max_length=300, blank=True)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = unique_slug(self, self.title)
        super().save(*args, **kwargs)
