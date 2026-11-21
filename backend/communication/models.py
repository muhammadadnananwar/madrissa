from django.conf import settings
from django.db import models
from django.utils import timezone

from academics.models import Section
from core.models import TimeStamped
from core.roles import Role

User = settings.AUTH_USER_MODEL


class Announcement(TimeStamped):
    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        IMPORTANT = "important", "Important"
        URGENT = "urgent", "Urgent"

    title = models.CharField(max_length=200)
    body = models.TextField()
    audience = models.JSONField(default=list, blank=True,
                                help_text=f"List of roles; empty = everyone. Roles: {', '.join(Role.values)}")
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.CASCADE,
                                help_text="Only for students/parents of this section")
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    attachment = models.FileField(upload_to="announcements/", null=True, blank=True)
    publish_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_pinned = models.BooleanField(default=False)
    notify = models.BooleanField(default=True, help_text="Send in-app notification to the audience")
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-is_pinned", "-publish_at"]

    def __str__(self):
        return self.title


class Notification(TimeStamped):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True)
    kind = models.CharField(max_length=30, default="info")
    link = models.CharField(max_length=300, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user}: {self.title}"


class Message(TimeStamped):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sent_messages")
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_messages")
    subject = models.CharField(max_length=200)
    body = models.TextField()
    attachment = models.FileField(upload_to="messages/", null=True, blank=True)
    reply_to = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies")
    read_at = models.DateTimeField(null=True, blank=True)
    deleted_by_sender = models.BooleanField(default=False)
    deleted_by_recipient = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender} → {self.recipient}: {self.subject}"


class Event(TimeStamped):
    class Kind(models.TextChoices):
        ISLAMIC = "islamic", "Islamic occasion"
        ACADEMIC = "academic", "Academic"
        JALSA = "jalsa", "Jalsa / Dastar-bandi"
        COMPETITION = "competition", "Competition"
        SPORTS = "sports", "Sports"
        MEETING = "meeting", "Meeting"
        PTM = "ptm", "Parent-teacher meeting"
        OTHER = "other", "Other"

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True)
    kind = models.CharField(max_length=15, choices=Kind.choices, default=Kind.OTHER)
    description = models.TextField(blank=True)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    location = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to="events/", null=True, blank=True)
    audience = models.JSONField(default=list, blank=True, help_text="Roles; empty = everyone")
    is_public = models.BooleanField(default=False, help_text="Show on the public website")
    content = models.TextField(blank=True, help_text="Full details for the website event page (blank lines separate paragraphs)")
    registration_link = models.URLField(blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-start"]

    def __str__(self):
        return self.title


class Complaint(TimeStamped):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        IN_PROGRESS = "in_progress", "In progress"
        RESOLVED = "resolved", "Resolved"
        CLOSED = "closed", "Closed"

    class Category(models.TextChoices):
        ACADEMIC = "academic", "Academic"
        HOSTEL = "hostel", "Hostel / Mess"
        FEE = "fee", "Fees"
        TRANSPORT = "transport", "Transport"
        STAFF = "staff", "Staff conduct"
        FACILITY = "facility", "Facility / maintenance"
        SUGGESTION = "suggestion", "Suggestion"
        OTHER = "other", "Other"

    submitted_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="complaints")
    category = models.CharField(max_length=12, choices=Category.choices, default=Category.OTHER)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    is_anonymous = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.OPEN)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_complaints")
    resolution = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject


class ParentMeeting(TimeStamped):
    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        SCHEDULED = "scheduled", "Scheduled"
        DONE = "done", "Held"
        CANCELLED = "cancelled", "Cancelled"

    student = models.ForeignKey("people.Student", on_delete=models.CASCADE, related_name="parent_meetings")
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="parent_meetings")
    scheduled_at = models.DateTimeField(null=True, blank=True)
    agenda = models.CharField(max_length=255)
    minutes = models.TextField(blank=True, help_text="Discussion notes / outcome")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.REQUESTED)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-scheduled_at"]

    def __str__(self):
        return f"PTM {self.student} with {self.teacher}"
