"""Mark enrolled people with no punch as absent. Schedule nightly, e.g. 23:30."""
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from attendance.biometric import close_day, reprocess


class Command(BaseCommand):
    help = "Close a biometric attendance day (default: today)"

    def add_arguments(self, parser):
        parser.add_argument("--date", type=date.fromisoformat, default=None)
        parser.add_argument("--students", action="store_true", help="Also mark students without a punch absent")
        parser.add_argument("--no-staff", action="store_true")

    def handle(self, *args, **o):
        d = o["date"] or timezone.localdate()
        reprocess(d)
        r = close_day(d, staff=not o["no_staff"], students=o["students"])
        self.stdout.write(r.get("detail") or f"{d}: {r['staff']} staff and {r['students']} student(s) marked absent")
