from datetime import datetime, timedelta

from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from communication.services import notify
from core.audit import audit
from core.roles import ACADEMIC, ALL, R, has_role, is_admin
from core.scopes import children_qs
from core.viewsets import BaseModelViewSet
from lms.services import student_course_ids

from . import providers
from . import serializers as s
from .models import LiveClass, LiveClassParticipant

MANAGERS = ACADEMIC + [R.TEACHER]


def _student_filter(student_user):
    sp = getattr(student_user, "student_profile", None)
    q = Q(course_id__in=student_course_ids(student_user))
    if sp and sp.section_id:
        q |= Q(section_id=sp.section_id)
    return q


def live_scope(qs, user):
    if user.role == R.TEACHER:
        return qs.filter(teacher=user)
    if user.role == R.STUDENT:
        return qs.filter(_student_filter(user))
    if user.role == R.PARENT:
        q = Q(pk__in=[])
        for st in children_qs(user).select_related("user"):
            q |= _student_filter(st.user)
        return qs.filter(q)
    return qs.none()


def can_manage(user, lc):
    return is_admin(user) or has_role(user, ACADEMIC) or lc.teacher_id == user.id


def mark_attendance(lc, user, status):
    """Live-class attendance is written as subject-wise attendance for the class day."""
    from attendance.models import Source, StudentAttendance
    sp = getattr(user, "student_profile", None)
    if not sp:
        return
    StudentAttendance.objects.update_or_create(
        student=sp, date=timezone.localtime(lc.scheduled_start).date(), subject=lc.subject,
        defaults={"section_id": lc.section_id or sp.section_id, "status": status, "source": Source.LIVE_CLASS,
                  "remarks": f"Live class #{lc.id}", "marked_by": lc.teacher})


class LiveClassViewSet(BaseModelViewSet):
    queryset = LiveClass.objects.all()
    serializer_class = s.LiveClassSerializer
    resource_key = "live-classes"
    read_roles = ACADEMIC
    write_roles = MANAGERS
    scope = staticmethod(live_scope)
    search_fields = ["title", "description"]
    filterset_fields = ["status", "provider", "section", "course", "teacher", "subject"]
    label, group, icon, menu = "Live Classes", "Learning (LMS)", "video", False
    list_fields = ["title", "scheduled_start", "teacher", "section", "course", "provider", "status"]
    ui_actions = [
        {"name": "join", "roles": ALL, "row": False}, {"name": "leave", "roles": ALL, "row": False},
        {"name": "end", "roles": MANAGERS, "label": "End class", "confirm": "End this class and finalise attendance?"},
        {"name": "cancel", "roles": MANAGERS, "label": "Cancel class", "style": "danger", "confirm": "Cancel this class?"},
        {"name": "regenerate", "roles": MANAGERS, "label": "New meeting link"},
        {"name": "report", "roles": MANAGERS, "row": False},
    ]

    def validate_create(self, serializer, extra):
        if self.request.user.role == R.TEACHER or not serializer.validated_data.get("teacher"):
            extra["teacher"] = self.request.user

    def after_save(self, obj, created):
        if created or not obj.join_url:
            obj.provider_error = providers.provision(obj)[:300]
            obj.save()
            if created:
                notify(list(obj.participant_users()), f"Live class scheduled: {obj.title}",
                       f"{timezone.localtime(obj.scheduled_start):%a %d %b, %H:%M} with {obj.teacher.display_name}",
                       f"/live/room?id={obj.id}", "live_class")

    def perform_destroy(self, instance):
        providers.cancel(instance)
        super().perform_destroy(instance)

    def _managed(self):
        lc = self.get_object()
        if not can_manage(self.request.user, lc):
            raise PermissionDenied()
        return lc

    @action(detail=True, methods=["post"])
    def join(self, request, pk=None):
        lc = self.get_object()
        user = request.user
        manager = can_manage(user, lc)
        if lc.status == LiveClass.Status.CANCELLED:
            raise ValidationError({"detail": "This class was cancelled."})
        if lc.status == LiveClass.Status.COMPLETED and not manager:
            return Response({"detail": "This class has ended.", "recording_url": lc.recording_url, "ended": True}, status=400)
        opens_at = lc.scheduled_start - timedelta(minutes=15)
        if not manager and timezone.now() < opens_at:
            raise ValidationError({"detail": f"Class opens at {timezone.localtime(opens_at):%H:%M}."})
        if not lc.join_url:
            lc.provider_error = providers.provision(lc)
            lc.save()
            if lc.provider_error:
                raise ValidationError({"detail": f"Meeting link unavailable: {lc.provider_error}"})
        now = timezone.now()
        if lc.teacher_id == user.id and lc.status == LiveClass.Status.SCHEDULED:
            lc.status, lc.actual_start = LiveClass.Status.LIVE, now
            lc.save(update_fields=["status", "actual_start", "updated_at"])
        p, created = LiveClassParticipant.objects.get_or_create(live_class=lc, user=user, defaults={"joined_at": now})
        if not created:
            p.join_count += 1
            p.left_at = None
            p.save(update_fields=["join_count", "left_at", "updated_at"])
        if lc.auto_attendance and user.role == R.STUDENT:
            late = lc.actual_start and now > lc.actual_start + timedelta(minutes=10)
            mark_attendance(lc, user, "late" if late else "present")
        return Response({
            "provider": lc.provider, "join_url": lc.host_url if manager and lc.host_url else lc.join_url,
            "passcode": lc.passcode, "embed": lc.provider == "jitsi" and settings.JITSI_EMBED,
            "jitsi_domain": settings.JITSI_DOMAIN, "room": lc.meeting_id if lc.provider == "jitsi" else None,
            "display_name": user.display_name, "email": user.email, "is_host": manager,
            "title": lc.title, "status": lc.status,
        })

    @action(detail=True, methods=["post"])
    def leave(self, request, pk=None):
        lc = self.get_object()
        LiveClassParticipant.objects.filter(live_class=lc, user=request.user).update(left_at=timezone.now())
        return Response({"detail": "Left."})

    @action(detail=True, methods=["post"])
    def end(self, request, pk=None):
        lc = self._managed()
        ser = s.EndClassSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        now = timezone.now()
        lc.status, lc.actual_end = LiveClass.Status.COMPLETED, now
        if ser.validated_data.get("recording_url"):
            lc.recording_url = ser.validated_data["recording_url"]
        lc.save()
        LiveClassParticipant.objects.filter(live_class=lc, left_at__isnull=True).update(left_at=now)
        absent = 0
        if lc.auto_attendance:
            joined = set(lc.participants.values_list("user_id", flat=True))
            for u in lc.participant_users().exclude(id__in=joined):
                mark_attendance(lc, u, "absent")
                absent += 1
        audit(request, "end", lc, "live-classes")
        return Response({"detail": f"Class ended. {absent} student(s) marked absent."})

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        lc = self._managed()
        providers.cancel(lc)
        lc.status = LiveClass.Status.CANCELLED
        lc.save(update_fields=["status", "updated_at"])
        notify(list(lc.participant_users()), f"Live class cancelled: {lc.title}",
               f"Scheduled {timezone.localtime(lc.scheduled_start):%a %d %b %H:%M}", "/live", "live_class")
        return Response({"detail": "Class cancelled and students notified."})

    @action(detail=True, methods=["post"])
    def regenerate(self, request, pk=None):
        lc = self._managed()
        lc.join_url = ""
        lc.provider_error = providers.provision(lc)
        lc.save()
        if lc.provider_error:
            return Response({"detail": lc.provider_error}, status=400)
        return Response({"detail": "New meeting link created.", "join_url": lc.join_url})

    @action(detail=True, methods=["get"])
    def report(self, request, pk=None):
        lc = self._managed()
        parts = {p.user_id: p for p in lc.participants.select_related("user")}
        rows = []
        for u in lc.participant_users():
            p = parts.pop(u.id, None)
            rows.append({"user": u.id, "name": u.display_name, "joined": bool(p), "joined_at": p.joined_at if p else None,
                         "left_at": p.left_at if p else None, "minutes": p.minutes if p else 0,
                         "joins": p.join_count if p else 0})
        for p in parts.values():
            rows.append({"user": p.user_id, "name": p.user.display_name, "joined": True, "joined_at": p.joined_at,
                         "left_at": p.left_at, "minutes": p.minutes, "joins": p.join_count, "guest": True})
        return Response({"class": {"id": lc.id, "title": lc.title, "status": lc.status, "actual_start": lc.actual_start,
                                   "actual_end": lc.actual_end},
                         "rows": rows, "present": sum(1 for r in rows if r["joined"]), "total": len(rows)})


class LiveClassParticipantViewSet(BaseModelViewSet):
    queryset = LiveClassParticipant.objects.all()
    serializer_class = s.LiveClassParticipantSerializer
    resource_key = "live-participants"
    read_roles = ACADEMIC
    read_only = True
    scope = staticmethod(lambda qs, u: qs.filter(Q(user=u) | Q(live_class__teacher=u)))
    label, group, icon, menu = "Live Class Participation", "Learning (LMS)", "users", False
    list_fields = ["live_class", "user", "joined_at", "left_at", "join_count"]


class UpcomingClassesView(APIView):
    def get(self, request):
        user = request.user
        qs = LiveClass.objects.select_related("teacher", "section", "course", "subject")
        if not has_role(user, ACADEMIC):
            qs = live_scope(qs, user)
        now = timezone.now()
        if request.query_params.get("scope", "upcoming") == "upcoming":
            qs = qs.filter(scheduled_start__gte=now - timedelta(hours=3)).exclude(
                status__in=["completed", "cancelled"]).order_by("scheduled_start")
        else:
            qs = qs.filter(Q(status="completed") | Q(scheduled_start__lt=now - timedelta(hours=3))).order_by("-scheduled_start")
        return Response([{
            "id": lc.id, "title": lc.title, "description": lc.description, "scheduled_start": lc.scheduled_start,
            "duration_minutes": lc.duration_minutes, "teacher": lc.teacher.display_name,
            "section": str(lc.section) if lc.section else None, "course": lc.course.title if lc.course else None,
            "subject": lc.subject.name if lc.subject else None, "provider": lc.provider,
            "provider_display": lc.get_provider_display(), "status": lc.status, "recording_url": lc.recording_url,
            "can_manage": can_manage(user, lc), "provider_error": lc.provider_error,
            "opens_at": lc.scheduled_start - timedelta(minutes=15),
        } for lc in qs[:100]])


class RecurringScheduleView(APIView):
    """Create a weekly series of live classes."""

    def post(self, request):
        user = request.user
        if not has_role(user, MANAGERS):
            raise PermissionDenied()
        ser = s.RecurringScheduleSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        teacher_id = d.get("teacher") if has_role(user, ACADEMIC) and d.get("teacher") else user.id
        tz = timezone.get_current_timezone()
        weekdays = set(d["weekdays"])
        created, day = [], d["start_date"]
        while day <= d["end_date"]:
            if day.weekday() in weekdays:
                lc = LiveClass(title=d["title"], description=d["description"], section_id=d.get("section"),
                               course_id=d.get("course"), subject_id=d.get("subject"), teacher_id=teacher_id,
                               provider=d["provider"], duration_minutes=d["duration_minutes"],
                               scheduled_start=datetime.combine(day, d["time"], tzinfo=tz),
                               auto_attendance=d["auto_attendance"])
                lc.provider_error = providers.provision(lc)
                lc.save()
                created.append(lc)
            day += timedelta(days=1)
        if created:
            notify(list(created[0].participant_users()), f"{len(created)} live classes scheduled: {d['title']}",
                   f"Starting {timezone.localtime(created[0].scheduled_start):%a %d %b %H:%M}", "/live", "live_class")
        return Response({"detail": f"{len(created)} class(es) scheduled.", "ids": [c.id for c in created]})


class ProviderStatusView(APIView):
    def get(self, request):
        return Response(providers.status())
