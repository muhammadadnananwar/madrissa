from django.conf import settings
from django.db import models

from academics.models import Section, Subject
from core.models import TimeStamped
from lms.models import Course

User = settings.AUTH_USER_MODEL


class LiveClass(TimeStamped):
    class Provider(models.TextChoices):
        JITSI = "jitsi", "Jitsi Meet (free)"
        GOOGLE_MEET = "google_meet", "Google Meet"
        ZOOM = "zoom", "Zoom"
        CUSTOM = "custom", "Custom link"

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        LIVE = "live", "Live now"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, null=True, blank=True, on_delete=models.SET_NULL, related_name="live_classes")
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL, related_name="live_classes")
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL)
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name="live_classes")
    provider = models.CharField(max_length=12, choices=Provider.choices, default=Provider.JITSI)
    scheduled_start = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=45)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    meeting_id = models.CharField(max_length=200, blank=True)
    join_url = models.URLField(max_length=500, blank=True, help_text="Auto-generated unless provider is 'custom'")
    host_url = models.URLField(max_length=800, blank=True)
    passcode = models.CharField(max_length=40, blank=True)
    recording_url = models.URLField(max_length=500, blank=True)
    auto_attendance = models.BooleanField(default=True, help_text="Mark attendance automatically when students join")
    actual_start = models.DateTimeField(null=True, blank=True, editable=False)
    actual_end = models.DateTimeField(null=True, blank=True, editable=False)
    provider_error = models.CharField(max_length=300, blank=True, editable=False)

    class Meta:
        ordering = ["-scheduled_start"]
        verbose_name_plural = "live classes"

    def __str__(self):
        return f"{self.title} @ {self.scheduled_start:%Y-%m-%d %H:%M}"

    def participant_users(self):
        from accounts.models import User as U
        ids = set()
        if self.course_id:
            ids |= set(self.course.student_users().values_list("id", flat=True))
        if self.section_id:
            ids |= set(self.section.students.filter(status="active").values_list("user_id", flat=True))
        return U.objects.filter(id__in=ids)


class LiveClassParticipant(TimeStamped):
    live_class = models.ForeignKey(LiveClass, on_delete=models.CASCADE, related_name="participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="live_participations")
    joined_at = models.DateTimeField()
    left_at = models.DateTimeField(null=True, blank=True)
    join_count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("live_class", "user")
        ordering = ["joined_at"]

    def __str__(self):
        return f"{self.user.display_name} in {self.live_class}"

    @property
    def minutes(self):
        if self.left_at:
            return round((self.left_at - self.joined_at).total_seconds() / 60)
        return None
