"""
Re-check every active student against the strike-off rule (normally applied the moment an absence is saved).

    python manage.py apply_attendance_rules            # up to today
    python manage.py apply_attendance_rules --date 2026-11-20
"""
import datetime

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_date

from attendance.rules import apply_student_strike_off
from people.models import Student


class Command(BaseCommand):
    help = "Strike off students with too many consecutive uninformed absences (limit set in Institution Settings)."

    def add_arguments(self, parser):
        parser.add_argument("--date", help="Check up to this date (YYYY-MM-DD); default today")

    def handle(self, *args, date=None, **opts):
        upto = parse_date(date) if date else datetime.date.today()
        count = sum(apply_student_strike_off(st, upto) for st in Student.objects.filter(status="active").select_related("user"))
        self.stdout.write(self.style.SUCCESS(f"{count} student(s) struck off."))
