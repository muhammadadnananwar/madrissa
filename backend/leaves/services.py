from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from academics.models import AcademicYear
from attendance.services import is_holiday
from core.roles import ACADEMIC, ADMINS, HR, R, STUDENT_SIDE, has_role, is_admin
from core.scopes import teacher_section_ids

from .models import LeaveRequest

APPROVERS = HR + ACADEMIC + [R.TEACHER, R.HOSTEL_WARDEN]


def can_approve(user, leave):
    """Students: class teacher / academic staff / warden. Staff: HR & management (never yourself)."""
    if is_admin(user):
        return True
    applicant = leave.user
    if applicant.role in STUDENT_SIDE:
        if has_role(user, ACADEMIC + [R.HOSTEL_WARDEN]):
            return True
        sp = getattr(applicant, "student_profile", None)
        return bool(user.role == R.TEACHER and sp and sp.section_id in teacher_section_ids(user))
    if applicant.id == user.id:
        return False
    return has_role(user, HR + ADMINS)


def working_days(leave):
    d = leave.start_date
    while d <= leave.end_date:
        if not is_holiday(d):
            yield d
        d += timedelta(days=1)


@transaction.atomic
def sync_attendance(leave, by):
    """Approved leave -> mark 'leave' (or half day) in attendance for each working day."""
    from attendance.models import Source, StaffAttendance, StudentAttendance
    sp = getattr(leave.user, "student_profile", None)
    ep = getattr(leave.user, "employee_profile", None)
    status = "half_day" if leave.half_day else "leave"
    for d in working_days(leave):
        if sp:
            StudentAttendance.objects.update_or_create(
                student=sp, date=d, subject=None,
                defaults={"section_id": sp.section_id, "status": status, "source": Source.LEAVE, "marked_by": by,
                          "remarks": f"Leave #{leave.id}"})
        if ep:
            StaffAttendance.objects.update_or_create(
                employee=ep, date=d, defaults={"status": status, "source": Source.LEAVE, "marked_by": by,
                                               "remarks": f"Leave #{leave.id}"})


def undo_attendance(leave):
    from attendance.models import StaffAttendance, StudentAttendance
    StudentAttendance.objects.filter(student__user=leave.user, remarks=f"Leave #{leave.id}").delete()
    StaffAttendance.objects.filter(employee__user=leave.user, remarks=f"Leave #{leave.id}").delete()


def used_days(user, leave_type, year=None):
    year = year or AcademicYear.current()
    qs = LeaveRequest.objects.filter(user=user, leave_type=leave_type, status="approved")
    if year:
        qs = qs.filter(start_date__gte=year.start_date, start_date__lte=year.end_date)
    else:
        qs = qs.filter(start_date__year=timezone.localdate().year)
    return sum(l.days for l in qs)
