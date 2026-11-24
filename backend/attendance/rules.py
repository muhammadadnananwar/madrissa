"""
Rules for uninformed absences (attendance status "Absent").

Approved leave ("On leave"), "Excused", holidays and days off never count; neither does a day with no record.
Limits and fine amounts come from Institution Settings (website.SiteSettings) and are edited in the portal.

* Students: N consecutive working days Absent  ->  status "Struck off" (reinstate with "Change status").
* Staff: more than the allowed uninformed absences in a month  ->  a fine on that month's payslip
  (percentage of basic salary or a fixed amount, per extra absence or once a month).
"""
import calendar
import contextlib
import contextvars
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Q

from accounts.models import User
from core.roles import R

_muted = contextvars.ContextVar("attendance_rules_muted", default=False)


@contextlib.contextmanager
def muted():
    """Temporarily switch the automatic rules off (bulk imports, demo data)."""
    token = _muted.set(True)
    try:
        yield
    finally:
        _muted.reset(token)


def _settings():
    from website.models import SiteSettings
    return SiteSettings.get()


def _is_working_day(d, weekdays, holidays):
    return d.weekday() in weekdays and d not in holidays


def _holidays_between(start, end):
    from academics.models import Holiday
    days = set()
    for h in Holiday.objects.filter(start_date__lte=end, end_date__gte=start):
        d = max(h.start_date, start)
        while d <= min(h.end_date, end):
            days.add(d)
            d += timedelta(days=1)
    return days


# ------------------------------------------------------------------------------------------- students

def consecutive_absences(student, upto, limit=60):
    """Working days marked Absent in a row, counting back from `upto` (inclusive). Returns the list of dates."""
    from .models import StudentAttendance
    weekdays = _settings().working_weekdays()
    start = upto - timedelta(days=limit * 2)
    holidays = _holidays_between(start, upto)
    status_by_day = dict(StudentAttendance.objects.filter(student=student, subject__isnull=True, date__range=(start, upto))
                         .values_list("date", "status"))
    streak, d = [], upto
    while d >= start and len(streak) < limit:
        if _is_working_day(d, weekdays, holidays):
            if status_by_day.get(d) != "absent":
                break
            streak.append(d)
        d -= timedelta(days=1)
    return streak


def apply_student_strike_off(student, upto=None):
    """Strike the student off when the consecutive-absence limit is reached. Returns True if the status changed."""
    from communication.services import notify
    from people.models import Student
    cfg = _settings()
    if _muted.get() or not cfg.strike_off_enabled or student.status != Student.Status.ACTIVE:
        return False
    limit = max(1, cfg.strike_off_after_days)
    streak = consecutive_absences(student, upto or date.today(), limit=limit)
    if len(streak) < limit:
        return False
    first, last = min(streak), max(streak)
    student.status = Student.Status.STRUCK_OFF
    student.leaving_date = last
    student.leaving_reason = (f"Struck off automatically: absent without leave for {len(streak)} consecutive working days "
                              f"({first:%d %b} – {last:%d %b %Y})")[:200]
    student.save(update_fields=["status", "leaving_date", "leaving_reason", "updated_at"])
    name = student.user.display_name
    title = f"Name struck off: {name}"
    body = f"{student.admission_no} — absent without leave {first:%d %b} to {last:%d %b %Y} ({len(streak)} days)."
    staff = list(User.objects.filter(is_active=True, role__in=[R.PRINCIPAL, R.ADMIN, R.ACADEMIC_COORDINATOR]))
    if student.section_id and getattr(student.section, "class_teacher_id", None):
        staff.append(student.section.class_teacher)
    notify(staff, title, body, f"/m/students/{student.id}", "attendance")
    if student.guardian_id and getattr(student.guardian, "user_id", None):
        notify(student.guardian.user, title, body + " Please contact the Jamia office for reinstatement.", "", "attendance")
    notify(student.user, title, "Please contact the Jamia office.", "", "attendance")
    return True


# ---------------------------------------------------------------------------------------------- staff

def month_bounds(day):
    first = day.replace(day=1)
    return first, first.replace(day=calendar.monthrange(first.year, first.month)[1])


def uninformed_absences(employee, month):
    """Dates in the month the employee was marked Absent (approved leave is recorded as 'leave', not counted)."""
    from .models import StaffAttendance
    first, last = month_bounds(month)
    return sorted(StaffAttendance.objects.filter(employee=employee, date__range=(first, last), status="absent")
                  .values_list("date", flat=True))


def penalty_applies(employee, cfg=None):
    cfg = cfg or _settings()
    if not cfg.staff_penalty_enabled or employee.employment_type == "volunteer":
        return False
    return cfg.staff_penalty_scope == "all" or employee.kind == "teaching"


def absence_penalty(employee, month, cfg=None):
    """Fine for uninformed absences above the monthly limit -> (amount, details dict)."""
    cfg = cfg or _settings()
    days = uninformed_absences(employee, month)
    limit = cfg.staff_absence_limit
    extra = max(0, len(days) - limit)
    details = {"uninformed_absences": len(days), "allowed": limit, "extra": extra, "dates": [d.isoformat() for d in days],
               "type": cfg.staff_penalty_type, "value": str(cfg.staff_penalty_value), "per": cfg.staff_penalty_per}
    if not extra or not penalty_applies(employee, cfg):
        return Decimal("0"), {**details, "applied": False}
    unit = (employee.basic_salary * cfg.staff_penalty_value / 100 if cfg.staff_penalty_type == "percent"
            else cfg.staff_penalty_value)
    times = extra if cfg.staff_penalty_per == "per_day" else 1
    return (Decimal(unit) * times).quantize(Decimal("0.01")), {**details, "applied": True}


def warn_staff_over_limit(employee, day):
    """Tell the employee and HR when an absence takes them over the monthly limit (once, on the first extra day)."""
    from communication.services import notify
    cfg = _settings()
    if _muted.get() or not penalty_applies(employee, cfg):
        return
    days = uninformed_absences(employee, day)
    if len(days) != cfg.staff_absence_limit + 1:
        return
    amount, _ = absence_penalty(employee, day, cfg)
    what = (f"{cfg.staff_penalty_value}% of basic salary" if cfg.staff_penalty_type == "percent"
            else f"{cfg.staff_penalty_value}") + (" for each further absence" if cfg.staff_penalty_per == "per_day" else "")
    title = f"Uninformed absences over the limit — {day:%B %Y}"
    body = (f"{len(days)} absences without leave this month (allowed: {cfg.staff_absence_limit}). "
            f"A fine of {what} will be deducted from the salary (so far {amount}).")
    notify(employee.user, title, body, "/payslips", "attendance")
    notify(list(User.objects.filter(is_active=True).filter(Q(role=R.HR_MANAGER) | Q(role=R.PRINCIPAL))),
           f"{employee.user.display_name}: {title}", body, f"/m/employees/{employee.id}", "attendance")
