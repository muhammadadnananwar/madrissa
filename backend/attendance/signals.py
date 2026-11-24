"""Run the uninformed-absence rules whenever an Absent mark is saved (manual, biometric, live class, import...)."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import rules
from .models import StaffAttendance, StudentAttendance


@receiver(post_save, sender=StudentAttendance)
def student_absence(sender, instance, **kwargs):
    if instance.status == "absent" and instance.subject_id is None:
        rules.apply_student_strike_off(instance.student, instance.date)


@receiver(post_save, sender=StaffAttendance)
def staff_absence(sender, instance, **kwargs):
    if instance.status == "absent":
        rules.warn_staff_over_limit(instance.employee, instance.date)
