from django.conf import settings
from django.db import models
from django.utils import timezone

from academics.models import Section, Subject, TimeSlot
from core.models import TimeStamped
from people.models import Employee, Student

User = settings.AUTH_USER_MODEL


class Status(models.TextChoices):
    PRESENT = "present", "Present"
    ABSENT = "absent", "Absent"
    LATE = "late", "Late"
    LEAVE = "leave", "On leave"
    HALF_DAY = "half_day", "Half day"
    EXCUSED = "excused", "Excused"
    HOLIDAY = "holiday", "Holiday"


class Source(models.TextChoices):
    MANUAL = "manual", "Manual"
    SELF = "self", "Self check-in"
    LIVE_CLASS = "live_class", "Live class"
    LEAVE = "leave", "Approved leave"
    DEVICE = "device", "Biometric / RFID device"
    QR = "qr", "QR code"


class StudentAttendance(TimeStamped):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="attendance")
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL)
    date = models.DateField(default=timezone.localdate, db_index=True)
    subject = models.ForeignKey(Subject, null=True, blank=True, on_delete=models.SET_NULL,
                                help_text="Leave empty for daily attendance")
    time_slot = models.ForeignKey(TimeSlot, null=True, blank=True, on_delete=models.SET_NULL)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    source = models.CharField(max_length=12, choices=Source.choices, default=Source.MANUAL)
    remarks = models.CharField(max_length=200, blank=True)
    guardian_notified = models.BooleanField(default=False)
    marked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "student__admission_no"]
        verbose_name_plural = "student attendance"

    def __str__(self):
        return f"{self.student} {self.date} {self.status}"


class StaffAttendance(TimeStamped):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="attendance")
    date = models.DateField(default=timezone.localdate, db_index=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PRESENT)
    check_in = models.TimeField(null=True, blank=True)
    check_out = models.TimeField(null=True, blank=True)
    source = models.CharField(max_length=12, choices=Source.choices, default=Source.MANUAL)
    check_in_location = models.CharField(max_length=80, blank=True, help_text="lat,lng captured on self check-in")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    marked_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date"]
        unique_together = ("employee", "date")
        verbose_name_plural = "staff attendance"

    def __str__(self):
        return f"{self.employee} {self.date} {self.status}"

    @property
    def hours_worked(self):
        if self.check_in and self.check_out:
            from datetime import datetime
            d = datetime.combine(self.date, self.check_out) - datetime.combine(self.date, self.check_in)
            return round(d.total_seconds() / 3600, 2)
        return None


# ------------------------------------------------------------- biometrics
def _device_key():
    import secrets
    return secrets.token_urlsafe(24)


class BiometricDevice(TimeStamped):
    """A fingerprint / face / card attendance terminal (ZKTeco and compatible, or any brand via API/CSV)."""

    class Protocol(models.TextChoices):
        PUSH = "push", "Push — ZKTeco ADMS / iclock (device sends punches to the server)"
        PULL = "pull", "Pull — server fetches logs over LAN (ZK TCP 4370, needs pyzk)"
        API = "api", "API — vendor software / middleware posts punches"
        CSV = "csv", "Manual CSV / Excel import"

    class Audience(models.TextChoices):
        STAFF = "staff", "Staff only"
        STUDENTS = "students", "Students only"
        BOTH = "both", "Staff and students"

    name = models.CharField(max_length=100, help_text="e.g. Main gate, Staff room, Hostel")
    serial_number = models.CharField(max_length=60, unique=True, help_text="Device SN (Menu → System info)")
    protocol = models.CharField(max_length=6, choices=Protocol.choices, default=Protocol.PUSH)
    audience = models.CharField(max_length=10, choices=Audience.choices, default=Audience.BOTH)
    location = models.CharField(max_length=120, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text="For pull mode")
    port = models.PositiveIntegerField(default=4370)
    comm_key = models.PositiveIntegerField(default=0, help_text="Device communication password (pull mode)")
    api_key = models.CharField(max_length=60, unique=True, default=_device_key, editable=False,
                               help_text="Secret for the JSON punch API")
    is_active = models.BooleanField(default=True)
    last_seen = models.DateTimeField(null=True, blank=True, editable=False)
    last_punch_at = models.DateTimeField(null=True, blank=True, editable=False)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"{self.name} ({self.serial_number})"


class BiometricEnrollment(TimeStamped):
    """Links a person to their user ID (PIN) on the attendance machines."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="biometric")
    pin = models.CharField("Device user ID / PIN", max_length=20, unique=True)
    card_number = models.CharField(max_length=30, blank=True)
    fingerprint = models.BooleanField(default=False, help_text="Fingerprint enrolled on device")
    face = models.BooleanField(default=False, help_text="Face enrolled on device")
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["pin"]

    def __str__(self):
        return f"{self.pin} → {self.user.display_name}"


class BiometricPunch(TimeStamped):
    """Raw punch log received from a device (kept for audit; processed into attendance)."""

    class Direction(models.TextChoices):
        IN = "in", "Check in"
        OUT = "out", "Check out"
        UNKNOWN = "unknown", "Unspecified"

    class Result(models.TextChoices):
        PENDING = "pending", "Pending"
        APPLIED = "applied", "Applied to attendance"
        UNMATCHED = "unmatched", "Unknown PIN"
        SKIPPED = "skipped", "Skipped (leave / manual record / not in audience)"

    device = models.ForeignKey(BiometricDevice, null=True, blank=True, on_delete=models.SET_NULL, related_name="punches")
    pin = models.CharField(max_length=20, db_index=True)
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="punches")
    punched_at = models.DateTimeField(db_index=True)
    direction = models.CharField(max_length=8, choices=Direction.choices, default=Direction.UNKNOWN)
    verify_mode = models.CharField(max_length=20, blank=True, help_text="fingerprint / face / card / password")
    source = models.CharField(max_length=6, default="push")
    result = models.CharField(max_length=10, choices=Result.choices, default=Result.PENDING, db_index=True)
    note = models.CharField(max_length=200, blank=True)
    raw = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-punched_at"]
        unique_together = ("device", "pin", "punched_at")
        verbose_name_plural = "biometric punches"

    def __str__(self):
        return f"{self.pin} @ {self.punched_at:%Y-%m-%d %H:%M}"
