from django.apps import AppConfig


class AttendanceConfig(AppConfig):
    name = "attendance"
    verbose_name = "Attendance"
    default_auto_field = "django.db.models.BigAutoField"

    def ready(self):
        from . import signals  # noqa: F401
