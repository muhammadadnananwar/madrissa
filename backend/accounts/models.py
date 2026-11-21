from django.contrib.auth.models import AbstractUser
from django.db import models

from core.roles import Role, STUDENT_SIDE


class Gender(models.TextChoices):
    MALE = "male", "Male"
    FEMALE = "female", "Female"


class User(AbstractUser):
    role = models.CharField(max_length=30, choices=Role.choices, default=Role.STUDENT, db_index=True)
    phone = models.CharField(max_length=30, blank=True)
    whatsapp = models.CharField(max_length=30, blank=True)
    cnic = models.CharField("CNIC / B-Form / National ID", max_length=30, blank=True)
    gender = models.CharField(max_length=10, choices=Gender.choices, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    father_name = models.CharField(max_length=150, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=80, blank=True)
    photo = models.ImageField(upload_to="users/photos/", null=True, blank=True)
    name_arabic = models.CharField("Name (Arabic / Urdu)", max_length=150, blank=True)
    must_change_password = models.BooleanField(default=False)
    last_seen = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["first_name", "last_name"]

    def __str__(self):
        name = self.get_full_name() or self.username
        return f"{name} ({self.get_role_display().split(' (')[0]})"

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    @property
    def is_staff_member(self):
        return self.role not in STUDENT_SIDE
