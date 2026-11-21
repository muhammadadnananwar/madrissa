"""Download new punches from LAN (pull-mode) ZK devices. Schedule e.g. every 5 minutes with cron."""
from django.core.management.base import BaseCommand

from attendance.biometric import BiometricError, pull_device
from attendance.models import BiometricDevice


class Command(BaseCommand):
    help = "Pull attendance logs from biometric devices configured in pull mode"

    def handle(self, *args, **opts):
        for device in BiometricDevice.objects.filter(protocol="pull", is_active=True):
            try:
                r = pull_device(device)
                self.stdout.write(f"{device}: {r['new']} new, {r['applied']} applied, {r['unmatched']} unknown PIN")
            except BiometricError as e:
                self.stderr.write(f"{device}: {e}")
