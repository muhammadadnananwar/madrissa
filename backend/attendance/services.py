"""Attendance helpers reused by leaves, exams, finance and live classes."""
from academics.models import Holiday


def is_holiday(d):
    from website.models import SiteSettings
    if d.weekday() not in SiteSettings.get().working_weekdays():
        return True
    return Holiday.objects.filter(start_date__lte=d, end_date__gte=d).exists()


def attendance_percentage(summary):
    """summary: {status: count} -> percentage of attended (late counts present, half day = 0.5)."""
    total = sum(summary.values())
    if not total:
        return None
    present = summary.get("present", 0) + summary.get("late", 0) + summary.get("half_day", 0) * 0.5
    counted = total - summary.get("holiday", 0)
    return round(present / counted * 100, 1) if counted else None
