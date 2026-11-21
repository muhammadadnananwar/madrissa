from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStamped
from people.models import Student

User = settings.AUTH_USER_MODEL


class Hostel(TimeStamped):
    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=[("male", "Baneen"), ("female", "Banaat")], default="male")
    warden = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="hostels_managed")
    address = models.CharField(max_length=200, blank=True)
    capacity = models.PositiveIntegerField(default=50)

    def __str__(self):
        return self.name


class HostelRoom(TimeStamped):
    hostel = models.ForeignKey(Hostel, on_delete=models.CASCADE, related_name="rooms")
    number = models.CharField(max_length=20)
    floor = models.CharField(max_length=20, blank=True)
    capacity = models.PositiveIntegerField(default=4)
    notes = models.CharField(max_length=200, blank=True)

    class Meta:
        unique_together = ("hostel", "number")
        ordering = ["hostel", "number"]

    def __str__(self):
        return f"{self.hostel.name} / Room {self.number}"

    @property
    def occupied(self):
        return self.allocations.filter(is_active=True).count()


class HostelAllocation(TimeStamped):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="hostel_allocations")
    room = models.ForeignKey(HostelRoom, on_delete=models.CASCADE, related_name="allocations")
    bed_no = models.CharField(max_length=10, blank=True)
    from_date = models.DateField(default=timezone.localdate)
    to_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-from_date"]

    def __str__(self):
        return f"{self.student} → {self.room}"


class MessMenu(TimeStamped):
    class Meal(models.TextChoices):
        SEHRI = "sehri", "Sehri"
        BREAKFAST = "breakfast", "Breakfast"
        LUNCH = "lunch", "Lunch"
        IFTAR = "iftar", "Iftar"
        DINNER = "dinner", "Dinner"

    hostel = models.ForeignKey(Hostel, null=True, blank=True, on_delete=models.CASCADE)
    day = models.IntegerField(choices=[(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"),
                                       (4, "Friday"), (5, "Saturday"), (6, "Sunday")])
    meal = models.CharField(max_length=10, choices=Meal.choices)
    items = models.CharField(max_length=255)

    class Meta:
        ordering = ["day", "meal"]
        verbose_name_plural = "mess menu"

    def __str__(self):
        return f"{self.get_day_display()} {self.get_meal_display()}: {self.items}"


class GatePass(TimeStamped):
    """Outing / home-leave pass for boarders."""

    class Status(models.TextChoices):
        REQUESTED = "requested", "Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        OUT = "out", "Currently out"
        RETURNED = "returned", "Returned"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="gate_passes")
    reason = models.CharField(max_length=200)
    out_time = models.DateTimeField()
    expected_return = models.DateTimeField()
    actual_out = models.DateTimeField(null=True, blank=True)
    actual_return = models.DateTimeField(null=True, blank=True)
    escort_name = models.CharField(max_length=150, blank=True, help_text="Person collecting the student")
    escort_phone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.REQUESTED)
    applied_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+", editable=False)

    class Meta:
        ordering = ["-out_time"]

    def __str__(self):
        return f"{self.student} out {self.out_time:%Y-%m-%d}"


class RollCall(TimeStamped):
    """Night roll call of boarders."""

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="roll_calls")
    date = models.DateField(default=timezone.localdate)
    is_present = models.BooleanField(default=True)
    remarks = models.CharField(max_length=200, blank=True)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        unique_together = ("student", "date")
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student} {self.date}"
