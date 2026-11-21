from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import TimeStamped

User = settings.AUTH_USER_MODEL


class Vehicle(TimeStamped):
    registration_no = models.CharField(max_length=30, unique=True)
    kind = models.CharField(max_length=30, default="Van", help_text="Bus, Van, Coaster...")
    capacity = models.PositiveIntegerField(default=15)
    driver_name = models.CharField(max_length=150)
    driver_phone = models.CharField(max_length=30)
    driver_license = models.CharField(max_length=40, blank=True)
    insurance_expiry = models.DateField(null=True, blank=True)
    fitness_expiry = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.kind} {self.registration_no}"


class Route(TimeStamped):
    name = models.CharField(max_length=120)
    vehicle = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.SET_NULL, related_name="routes")
    monthly_fare = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class RouteStop(TimeStamped):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="stops")
    name = models.CharField(max_length=120)
    pickup_time = models.TimeField(null=True, blank=True)
    drop_time = models.TimeField(null=True, blank=True)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["route", "order"]

    def __str__(self):
        return f"{self.route.name}: {self.name}"


class TransportAssignment(TimeStamped):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transport_assignments",
                             help_text="Student or staff member")
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="assignments")
    stop = models.ForeignKey(RouteStop, null=True, blank=True, on_delete=models.SET_NULL)
    from_date = models.DateField(default=timezone.localdate)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.display_name} → {self.route}"
