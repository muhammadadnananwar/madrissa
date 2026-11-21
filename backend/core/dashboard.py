"""Role-aware dashboard: stat cards, charts and to-do lists for the portal home page."""
from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from .roles import (ACADEMIC, ADMINS, ADMISSION, EXAM, FINANCE, FRONT_DESK, HOSTEL, HR, IFTA, INVENTORY, LIBRARY, R,
                    TRANSPORT, WEBSITE, has_role)


def card(label, value, icon="chart", link=None, tone="default"):
    return {"label": label, "value": value, "icon": icon, "link": link, "tone": tone}


def _attendance_trend(days=7):
    from attendance.models import StudentAttendance
    today = timezone.localdate()
    out = []
    for i in range(days - 1, -1, -1):
        d = today - timedelta(days=i)
        agg = dict(StudentAttendance.objects.filter(date=d, subject__isnull=True).values_list("status").annotate(c=Count("id")))
        total = sum(agg.values())
        present = agg.get("present", 0) + agg.get("late", 0)
        out.append({"label": d.strftime("%a %d"), "value": round(present / total * 100, 1) if total else None})
    return out


def _upcoming_live(user, limit=5):
    from liveclasses.models import LiveClass
    from liveclasses.views import live_scope
    qs = LiveClass.objects.filter(scheduled_start__gte=timezone.now() - timedelta(hours=2)).exclude(
        status__in=["completed", "cancelled"]).select_related("teacher", "section").order_by("scheduled_start")
    if not has_role(user, ACADEMIC):
        qs = live_scope(qs, user)
    return [{"id": l.id, "title": l.title, "start": l.scheduled_start, "teacher": l.teacher.display_name,
             "status": l.status, "section": str(l.section) if l.section else ""} for l in qs[:limit]]


def _today_timetable(user):
    from academics.models import TimetableEntry
    from core.scopes import children_qs
    qs = TimetableEntry.objects.filter(day=timezone.localdate().weekday()).select_related("time_slot", "subject", "teacher", "section", "room")
    if user.role == R.TEACHER:
        qs = qs.filter(teacher=user)
    elif user.role == R.STUDENT:
        sp = getattr(user, "student_profile", None)
        qs = qs.filter(section_id=sp.section_id if sp else None)
    elif user.role == R.PARENT:
        qs = qs.filter(section_id__in=children_qs(user).values_list("section_id", flat=True))
    else:
        return []
    return [{"time": f"{e.time_slot.start_time:%H:%M}-{e.time_slot.end_time:%H:%M}", "subject": e.subject.name if e.subject else e.note,
             "teacher": e.teacher.display_name if e.teacher else "", "section": str(e.section), "room": str(e.room or "")}
            for e in qs.order_by("time_slot__order")]


def _announcements(user, limit=5):
    from communication.views import visible_announcements
    return [{"id": a.id, "title": a.title, "priority": a.priority, "publish_at": a.publish_at}
            for a in visible_announcements(user).order_by("-is_pinned", "-publish_at")[:limit]]


def _events(limit=5):
    from communication.models import Event
    return [{"title": e.title, "start": e.start, "kind": e.get_kind_display()}
            for e in Event.objects.filter(start__gte=timezone.now()).order_by("start")[:limit]]


def _student_summary(st):
    from attendance.models import StudentAttendance
    from attendance.services import attendance_percentage
    from finance.models import Invoice
    from hifz.models import JuzProgress
    from hifz.services import overview as quran_overview
    summary = dict(StudentAttendance.objects.filter(student=st, subject__isnull=True).values_list("status").annotate(c=Count("id")))
    dues = Invoice.objects.filter(student=st, status__in=["unpaid", "partial"]).aggregate(t=Sum("total"), p=Sum("paid_amount"))
    return {"id": st.id, "user_id": st.user_id, "name": st.user.display_name, "admission_no": st.admission_no,
            "section": str(st.section) if st.section else "",
            "attendance": attendance_percentage(summary),
            "dues": (dues["t"] or 0) - (dues["p"] or 0),
            "juz_memorized": JuzProgress.objects.filter(student=st, program="hifz", status__in=["memorized", "tested"]).count(),
            "quran": quran_overview(st)}


def build_dashboard(request):
    from academics.models import Section
    from attendance.models import StaffAttendance, StudentAttendance
    from people.models import AdmissionApplication, Employee, Student

    user = request.user
    today = timezone.localdate()
    month_start = today.replace(day=1)
    data = {"role": user.role, "greeting": user.display_name, "cards": [], "lists": {}, "charts": {}}
    cards = data["cards"]

    if has_role(user, ADMINS + [R.ACADEMIC_COORDINATOR]):
        active = Student.objects.filter(status="active").count()
        att = dict(StudentAttendance.objects.filter(date=today, subject__isnull=True).values_list("status").annotate(c=Count("id")))
        marked = sum(att.values())
        cards += [
            card("Active students", active, "student", "/m/students"),
            card("Staff & teachers", Employee.objects.filter(status="active").count(), "briefcase", "/m/employees"),
            card("Present today", f"{att.get('present', 0) + att.get('late', 0)}/{marked}" if marked else "Not marked",
                 "check", "/attendance/overview"),
            card("Staff present", StaffAttendance.objects.filter(date=today, status__in=["present", "late"]).count(),
                 "check-circle", "/attendance/staff"),
            card("Sections", Section.objects.filter(academic_year__is_current=True).count(), "grid", "/m/sections"),
            card("New applications", AdmissionApplication.objects.filter(status="submitted").count(), "inbox", "/m/admissions", "warn"),
        ]
        data["charts"]["attendance_7d"] = _attendance_trend()
        unmarked = [str(sec) for sec in Section.objects.filter(academic_year__is_current=True)
                    if not StudentAttendance.objects.filter(section=sec, date=today, subject__isnull=True).exists()]
        data["lists"]["unmarked_sections"] = unmarked[:15]

    if has_role(user, FINANCE):
        from finance.models import Donation, Expense, Invoice, Payment
        fees = Payment.objects.filter(status="verified", date__gte=month_start).aggregate(s=Sum("amount"))["s"] or 0
        don = Donation.objects.filter(status="received", date__gte=month_start).aggregate(s=Sum("amount"))["s"] or 0
        exp = Expense.objects.filter(status="approved", date__gte=month_start).aggregate(s=Sum("amount"))["s"] or 0
        out = Invoice.objects.filter(status__in=["unpaid", "partial"]).aggregate(t=Sum("total"), p=Sum("paid_amount"))
        cards += [
            card("Fees this month", fees, "cash", "/finance", "good"),
            card("Donations this month", don, "hand", "/m/donations", "good"),
            card("Expenses this month", exp, "wallet", "/m/expenses"),
            card("Outstanding dues", (out["t"] or 0) - (out["p"] or 0), "receipt", "/finance/defaulters", "warn"),
            card("Proofs to verify", Payment.objects.filter(status="pending").count(), "upload", "/m/payments?status=pending", "warn"),
        ]

    if has_role(user, HR):
        from leaves.models import LeaveRequest
        cards += [card("Pending staff leaves", LeaveRequest.objects.filter(status="pending").exclude(
            user__role__in=[R.STUDENT, R.PARENT]).count(), "calendar-off", "/leaves", "warn"),
            card("On leave today", LeaveRequest.objects.filter(status="approved", start_date__lte=today,
                                                               end_date__gte=today).count(), "sun", "/leaves")]

    if has_role(user, ADMISSION) and not has_role(user, ADMINS):
        cards += [card("New applications", AdmissionApplication.objects.filter(status="submitted").count(), "inbox", "/m/admissions"),
                  card("Tests scheduled", AdmissionApplication.objects.filter(status="test_scheduled").count(), "calendar", "/m/admissions")]

    if has_role(user, EXAM) and user.role == R.EXAM_CONTROLLER:
        from exams.models import Exam, ExamPaper
        cards += [card("Upcoming papers", ExamPaper.objects.filter(date__gte=today).count(), "calendar", "/m/exam-papers"),
                  card("Unpublished exams", Exam.objects.filter(is_published=False).count(), "clipboard", "/m/exams")]

    if has_role(user, LIBRARY) and user.role == R.LIBRARIAN:
        from library.models import Book, BookIssue
        cards += [card("Books", Book.objects.count(), "book", "/m/books"),
                  card("Issued", BookIssue.objects.filter(status="issued").count(), "swap", "/m/book-issues"),
                  card("Overdue", BookIssue.objects.filter(status="issued", due_date__lt=today).count(), "alert", "/library", "warn")]

    if has_role(user, HOSTEL) and user.role == R.HOSTEL_WARDEN:
        from hostel.models import GatePass, HostelAllocation
        cards += [card("Boarders", HostelAllocation.objects.filter(is_active=True).count(), "bed", "/m/hostel-allocations"),
                  card("Out on gate pass", GatePass.objects.filter(status="out").count(), "exit", "/m/gate-passes"),
                  card("Pass requests", GatePass.objects.filter(status="requested").count(), "inbox", "/m/gate-passes", "warn")]

    if has_role(user, TRANSPORT) and user.role == R.TRANSPORT_MANAGER:
        from transport.models import TransportAssignment, Vehicle
        soon = today + timedelta(days=30)
        cards += [card("Vehicles", Vehicle.objects.filter(is_active=True).count(), "bus", "/m/vehicles"),
                  card("Transport users", TransportAssignment.objects.filter(is_active=True).count(), "users", "/m/transport-assignments"),
                  card("Documents expiring (30d)", Vehicle.objects.filter(Q(insurance_expiry__lte=soon) | Q(fitness_expiry__lte=soon)).count(),
                       "alert", "/m/vehicles", "warn")]

    if has_role(user, INVENTORY) and user.role == R.STORE_KEEPER:
        from django.db.models import F
        from inventory.models import Asset, StockItem
        cards += [card("Assets", Asset.objects.count(), "box", "/m/assets"),
                  card("Low stock items", StockItem.objects.filter(quantity__lte=F("reorder_level")).count(), "alert", "/m/stock-items", "warn")]

    if has_role(user, IFTA) and user.role == R.MUFTI:
        from website.models import FatwaQuestion
        cards += [card("New questions", FatwaQuestion.objects.filter(status="new").count(), "inbox", "/m/fatwas?status=new", "warn"),
                  card("Assigned to me", FatwaQuestion.objects.filter(assigned_to=user, status="assigned").count(), "scale", "/m/fatwas"),
                  card("Answered", FatwaQuestion.objects.filter(status="answered").count(), "check", "/m/fatwas")]

    if has_role(user, FRONT_DESK) and user.role == R.RECEPTIONIST:
        from people.models import VisitorLog
        from website.models import ContactMessage
        cards += [card("Visitors today", VisitorLog.objects.filter(check_in__date=today).count(), "door", "/m/visitors"),
                  card("Unresolved messages", ContactMessage.objects.filter(is_resolved=False).count(), "inbox", "/m/contact-messages")]

    if has_role(user, WEBSITE) and user.role == R.MEDIA_MANAGER:
        from website.models import ContactMessage, NewsPost
        cards += [card("News posts", NewsPost.objects.count(), "news", "/m/news"),
                  card("Unresolved messages", ContactMessage.objects.filter(is_resolved=False).count(), "inbox", "/m/contact-messages")]

    if user.role == R.TEACHER:
        from core.scopes import teacher_section_ids
        from lms.models import Course, Submission
        sections = teacher_section_ids(user)
        cards += [
            card("My sections", len(sections), "grid", "/attendance"),
            card("My students", Student.objects.filter(section_id__in=sections, status="active").count(), "student", "/m/students"),
            card("My courses", Course.objects.filter(Q(teacher=user) | Q(co_teachers=user)).distinct().count(), "graduation", "/lms"),
            card("To grade", Submission.objects.filter(assignment__course__teacher=user).exclude(status="graded").count(),
                 "clipboard", "/lms", "warn"),
        ]
        data["lists"]["unmarked_sections"] = [str(sec) for sec in Section.objects.filter(id__in=sections)
                                              if not StudentAttendance.objects.filter(section=sec, date=today, subject__isnull=True).exists()]

    if user.is_staff_member and getattr(user, "employee_profile", None):
        rec = StaffAttendance.objects.filter(employee=user.employee_profile, date=today).first()
        data["my_attendance"] = {"status": rec.status if rec else None, "check_in": rec.check_in if rec else None,
                                 "check_out": rec.check_out if rec else None}

    if user.role == R.STUDENT and getattr(user, "student_profile", None):
        s = _student_summary(user.student_profile)
        data["student"] = s
        cards += [card("Attendance", f"{s['attendance']}%" if s["attendance"] is not None else "—", "check", "/attendance"),
                  card("Fee dues", s["dues"], "receipt", "/fees", "warn" if s["dues"] else "good"),
                  card("Paras memorised", s["juz_memorized"], "quran", "/hifz")]

    if user.role == R.PARENT:
        from core.scopes import children_qs
        data["children"] = [_student_summary(st) for st in children_qs(user).select_related("user", "section")]

    if user.role in (R.STUDENT, R.PARENT):
        from lms.views import MyTasksView
        data["lists"]["tasks"] = MyTasksView().get(request).data[:8]

    data["lists"]["timetable_today"] = _today_timetable(user)
    data["lists"]["live_classes"] = _upcoming_live(user)
    data["lists"]["announcements"] = _announcements(user)
    data["lists"]["events"] = _events()
    from communication.models import Notification
    data["unread_notifications"] = Notification.objects.filter(user=user, is_read=False).count()
    return data
