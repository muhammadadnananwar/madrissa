from django.conf import settings
from django.db import models

from core.models import TimeStamped

User = settings.AUTH_USER_MODEL


class LeaveType(TimeStamped):
    class AppliesTo(models.TextChoices):
        STAFF = "staff", "Staff"
        STUDENT = "student", "Students"
        BOTH = "both", "Both"

    name = models.CharField(max_length=80, help_text="e.g. Casual, Sick, Hajj/Umrah, Maternity")
    code = models.CharField(max_length=10, unique=True)
    applies_to = models.CharField(max_length=10, choices=AppliesTo.choices, default=AppliesTo.BOTH)
    days_per_year = models.PositiveIntegerField(default=10, help_text="0 = unlimited")
    is_paid = models.BooleanField(default=True)
    requires_document = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class LeaveRequest(TimeStamped):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="leave_requests",
                             help_text="Person going on leave")
    applied_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    leave_type = models.ForeignKey(LeaveType, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    half_day = models.BooleanField(default=False)
    reason = models.TextField()
    document = models.FileField(upload_to="leaves/", null=True, blank=True)
    substitute = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="substitutions",
                                   help_text="Substitute teacher during leave")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING, db_index=True)
    reviewed_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+", editable=False)
    reviewed_at = models.DateTimeField(null=True, blank=True, editable=False)
    review_remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.display_name}: {self.leave_type} {self.start_date}→{self.end_date}"

    @property
    def days(self):
        if self.half_day:
            return 0.5
        return (self.end_date - self.start_date).days + 1
