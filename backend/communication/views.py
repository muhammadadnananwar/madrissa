from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from core.roles import ACADEMIC, ADMINS, ALL, R, STAFF_ROLES, STUDENT_SIDE, has_role, is_admin
from core.scopes import by_student, children_qs, teacher_section_ids
from core.viewsets import BaseModelViewSet

from . import serializers as s
from .models import Announcement, Complaint, Event, Message, Notification, ParentMeeting
from .services import notify

G = "Communication"
PUBLISHERS = ACADEMIC + [R.HR_MANAGER, R.ACCOUNTANT, R.EXAM_CONTROLLER, R.HOSTEL_WARDEN, R.MEDIA_MANAGER, R.TEACHER]


def user_sections(user):
    if user.role == R.STUDENT:
        sp = getattr(user, "student_profile", None)
        return {sp.section_id} if sp else set()
    if user.role == R.PARENT:
        return set(children_qs(user).values_list("section_id", flat=True))
    if user.role == R.TEACHER:
        return teacher_section_ids(user)
    return set()


def visible_announcements(user):
    now = timezone.now()
    qs = Announcement.objects.filter(publish_at__lte=now).filter(Q(expires_at__isnull=True) | Q(expires_at__gte=now))
    if is_admin(user):
        return qs
    qs = qs.filter(Q(audience=[]) | Q(audience__contains=[user.role]) | Q(created_by=user))
    sections = user_sections(user)
    return qs.filter(Q(section__isnull=True) | Q(section_id__in=sections) | Q(created_by=user))


def audience_users(a):
    qs = User.objects.filter(is_active=True)
    if a.audience:
        qs = qs.filter(role__in=a.audience)
    if a.section_id:
        ids = set(a.section.students.values_list("user_id", flat=True))
        ids |= set(User.objects.filter(Q(guardian_profile__students__section=a.section) |
                                       Q(class_teacher_of=a.section)).values_list("id", flat=True))
        staff = qs.filter(role__in=[r for r in (a.audience or []) if r not in STUDENT_SIDE])
        qs = qs.filter(Q(id__in=ids) | Q(id__in=staff.values("id")))
    return qs


class AnnouncementViewSet(BaseModelViewSet):
    queryset = Announcement.objects.all()
    serializer_class = s.AnnouncementSerializer
    resource_key = "announcements"
    read_roles = ACADEMIC
    write_roles = PUBLISHERS
    scope = staticmethod(lambda qs, user: visible_announcements(user))
    search_fields = ["title", "body"]
    label, group, icon, menu_roles = "Notice Board", G, "megaphone", PUBLISHERS
    list_fields = ["title", "priority", "audience", "section", "publish_at", "is_pinned", "created_by"]

    def validate_create(self, serializer, extra):
        sec = serializer.validated_data.get("section")
        if self.request.user.role == R.TEACHER and (not sec or sec.id not in teacher_section_ids(self.request.user)):
            raise ValidationError({"section": "Teachers may only announce to their own sections."})

    def after_save(self, obj, created):
        if created and obj.notify:
            notify(list(audience_users(obj).exclude(id=obj.created_by_id)), f"📢 {obj.title}", obj.body[:200],
                   "/announcements", "announcement")


class NotificationViewSet(BaseModelViewSet):
    """The current user's notifications (created by the system only)."""

    queryset = Notification.objects.all()
    serializer_class = s.NotificationSerializer
    resource_key = "notifications"
    permission_classes = [IsAuthenticated]
    scope = staticmethod(lambda qs, user: qs.filter(user=user))
    http_method_names = ["get", "post", "delete", "head", "options"]
    group, icon, menu = G, "bell", False
    list_fields = ["title", "kind", "is_read", "created_at"]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        raise PermissionDenied("Notifications are created by the system.")

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        self.get_queryset().filter(pk=pk).update(is_read=True)
        return Response({"detail": "ok"})

    @action(detail=False, methods=["post"])
    def read_all(self, request):
        self.get_queryset().filter(is_read=False).update(is_read=True)
        return Response({"detail": "All marked read."})

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        return Response({"count": self.get_queryset().filter(is_read=False).count()})


def can_message(sender, recipient):
    if sender.role in STUDENT_SIDE:
        return recipient.role in STAFF_ROLES
    return True


class MessageViewSet(BaseModelViewSet):
    """Internal messaging. Users only ever see their own messages."""

    queryset = Message.objects.all()
    serializer_class = s.MessageSerializer
    resource_key = "messages"
    permission_classes = [IsAuthenticated]
    scope = staticmethod(lambda qs, user: qs.filter(Q(sender=user) | Q(recipient=user)))
    http_method_names = ["get", "post", "delete", "head", "options"]
    group, icon, menu = G, "mail", False
    list_fields = ["subject", "sender", "recipient", "created_at", "read_at"]

    def get_queryset(self):
        u = self.request.user
        qs = Message.objects.select_related("sender", "recipient")
        box = self.request.query_params.get("box")
        if box == "sent":
            return qs.filter(sender=u, deleted_by_sender=False)
        if box == "inbox":
            return qs.filter(recipient=u, deleted_by_recipient=False)
        return qs.filter(Q(sender=u, deleted_by_sender=False) | Q(recipient=u, deleted_by_recipient=False))

    def validate_create(self, serializer, extra):
        r = serializer.validated_data["recipient"]
        if r.id == self.request.user.id:
            raise ValidationError({"recipient": "You cannot message yourself."})
        if not can_message(self.request.user, r):
            raise ValidationError({"recipient": "Students and parents can message staff members only."})
        parent = serializer.validated_data.get("reply_to")
        if parent and self.request.user.id not in (parent.sender_id, parent.recipient_id):
            raise ValidationError({"reply_to": "Invalid thread."})

    def after_save(self, obj, created):
        if created:
            notify(obj.recipient, f"New message from {obj.sender.display_name}", obj.subject, f"/messages?id={obj.id}", "message")

    def perform_destroy(self, instance):
        u = self.request.user
        if instance.sender_id == u.id:
            instance.deleted_by_sender = True
        if instance.recipient_id == u.id:
            instance.deleted_by_recipient = True
        instance.save()

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        m = self.get_object()
        if m.recipient_id == request.user.id and not m.read_at:
            m.read_at = timezone.now()
            m.save(update_fields=["read_at"])
        return Response({"detail": "ok"})

    @action(detail=True, methods=["get"])
    def thread(self, request, pk=None):
        root = self.get_object()
        while root.reply_to_id:
            root = root.reply_to
        msgs, frontier = [root], [root.id]
        while frontier:
            kids = list(Message.objects.filter(reply_to_id__in=frontier).select_related("sender", "recipient"))
            msgs += kids
            frontier = [k.id for k in kids]
        u = request.user
        msgs = sorted((x for x in msgs if u.id in (x.sender_id, x.recipient_id)), key=lambda x: x.created_at)
        return Response([{"id": x.id, "subject": x.subject, "body": x.body, "sender": x.sender.display_name,
                          "sender_id": x.sender_id, "recipient": x.recipient.display_name, "recipient_id": x.recipient_id,
                          "created_at": x.created_at, "read_at": x.read_at, "mine": x.sender_id == u.id,
                          "attachment": request.build_absolute_uri(x.attachment.url) if x.attachment else None}
                         for x in msgs])


class EventViewSet(BaseModelViewSet):
    queryset = Event.objects.all()
    serializer_class = s.EventSerializer
    resource_key = "events"
    read_roles, write_roles = ALL, ACADEMIC + [R.MEDIA_MANAGER]
    search_fields = ["title", "location"]
    label, group, icon, menu_roles = "Events Calendar", G, "calendar", ALL
    list_fields = ["title", "kind", "start", "end", "location", "is_public"]


class ComplaintViewSet(BaseModelViewSet):
    queryset = Complaint.objects.all()
    serializer_class = s.ComplaintSerializer
    resource_key = "complaints"
    read_roles = write_roles = ADMINS
    create_roles = ALL
    scope = staticmethod(lambda qs, user: qs.filter(Q(submitted_by=user) | Q(assigned_to=user)))
    owner_field = "submitted_by"
    label, group, icon, menu_roles = "Complaints & Suggestions", G, "flag", ALL
    list_fields = ["subject", "category", "status", "submitted_by", "assigned_to", "created_at"]

    def after_save(self, obj, created):
        if created:
            notify(list(User.objects.filter(role__in=[R.PRINCIPAL, R.ADMIN], is_active=True)), f"New complaint: {obj.subject}",
                   obj.get_category_display(), "/m/complaints", "complaint")
        elif obj.submitted_by_id and obj.status in ("resolved", "closed"):
            notify(obj.submitted_by, f"Complaint {obj.get_status_display().lower()}: {obj.subject}", obj.resolution[:200])


class ParentMeetingViewSet(BaseModelViewSet):
    queryset = ParentMeeting.objects.all()
    serializer_class = s.ParentMeetingSerializer
    resource_key = "parent-meetings"
    read_roles = ACADEMIC
    write_roles = ACADEMIC + [R.TEACHER]
    create_roles = [R.PARENT]
    scope = staticmethod(lambda qs, user: qs.filter(teacher=user) if user.role == R.TEACHER else by_student()(qs, user))
    label, group, icon = "Parent-Teacher Meetings", G, "handshake"
    menu_roles = ACADEMIC + [R.TEACHER, R.PARENT]
    list_fields = ["student", "teacher", "scheduled_at", "agenda", "status"]

    def validate_create(self, serializer, extra):
        user = self.request.user
        if user.role == R.PARENT and not children_qs(user).filter(pk=serializer.validated_data["student"].pk).exists():
            raise PermissionDenied("Not your child.")

    def after_save(self, obj, created):
        st = obj.student
        users = [obj.teacher] + [g.user for g in (st.guardian, st.second_guardian) if g and g.user_id]
        notify([u for u in users if u.id != self.request.user.id],
               f"Parent-teacher meeting {obj.get_status_display().lower()}", f"{st.user.display_name}: {obj.agenda}",
               "/m/parent-meetings", "ptm")


# ------------------------------------------------------------------ APIViews
class FeedView(APIView):
    def get(self, request):
        qs = visible_announcements(request.user).select_related("created_by", "section").order_by("-is_pinned", "-publish_at")[:50]
        return Response([{"id": a.id, "title": a.title, "body": a.body, "priority": a.priority, "is_pinned": a.is_pinned,
                          "publish_at": a.publish_at, "by": a.created_by.display_name if a.created_by else "",
                          "section": str(a.section) if a.section else None,
                          "attachment": request.build_absolute_uri(a.attachment.url) if a.attachment else None} for a in qs])


class CalendarView(APIView):
    """Events + holidays + exams + live classes (+ website calendar for web editors) between ?start and ?end.

    Returns {"items": [...], "can": {"event", "holiday", "web"}} so the portal calendar knows what the user may add/edit.
    """

    def get(self, request):
        from academics.models import Holiday
        from academics.views import HolidayViewSet
        from cms.models import CalendarItem
        from cms.views import CalendarItemViewSet
        from exams.models import ExamPaper
        from exams.services import paper_scope
        from liveclasses.models import LiveClass
        from liveclasses.views import live_scope
        today = timezone.localdate()
        try:
            start = datetime.strptime(request.query_params.get("start") or today.replace(day=1).isoformat(), "%Y-%m-%d").date()
            end = datetime.strptime(request.query_params.get("end") or (start + timedelta(days=42)).isoformat(), "%Y-%m-%d").date()
        except ValueError:
            raise ValidationError("start and end must be YYYY-MM-DD dates")
        user = request.user
        can = {"event": EventViewSet.can_write(user), "holiday": HolidayViewSet.can_write(user),
               "web": CalendarItemViewSet.can_write(user)}
        items = []

        events = Event.objects.filter(start__date__lte=end).filter(Q(end__date__gte=start) | Q(end__isnull=True, start__date__gte=start))
        if not (is_admin(user) or can["event"]):
            events = events.filter(Q(audience=[]) | Q(audience__contains=[user.role]))
        for e in events:
            items.append({"type": "event", "id": e.id, "title": e.title, "start": e.start, "end": e.end, "kind": e.get_kind_display(),
                          "kind_value": e.kind, "location": e.location, "description": e.description, "audience": e.audience,
                          "is_public": e.is_public, "editable": can["event"]})

        for h in Holiday.objects.filter(start_date__lte=end, end_date__gte=start):
            items.append({"type": "holiday", "id": h.id, "title": h.title, "start": h.start_date, "end": h.end_date,
                          "kind": h.get_kind_display(), "kind_value": h.kind, "description": h.description, "editable": can["holiday"]})

        if can["web"]:
            web = CalendarItem.objects.filter(start_date__lte=end).filter(
                Q(end_date__gte=start) | Q(end_date__isnull=True, start_date__gte=start))
            for c in web:
                items.append({"type": "web", "id": c.id, "title": c.title, "start": c.start_date, "end": c.end_date,
                              "kind": c.get_category_display(), "kind_value": c.category, "term": c.term,
                              "description": c.description, "is_published": c.is_published, "editable": True})

        papers = ExamPaper.objects.filter(date__range=(start, end)).select_related("subject", "exam", "section")
        if not has_role(user, ACADEMIC + [R.EXAM_CONTROLLER]):
            papers = paper_scope(papers, user)
        for p in papers[:300]:
            items.append({"type": "exam", "id": p.id, "title": f"{p.exam.name}: {p.subject.name}", "start": p.date,
                          "kind": str(p.section), "editable": False})

        classes = LiveClass.objects.filter(scheduled_start__date__range=(start, end)).exclude(status="cancelled")
        if not has_role(user, ACADEMIC):
            classes = live_scope(classes, user)
        for lc in classes[:300]:
            items.append({"type": "live", "id": lc.id, "title": lc.title, "start": lc.scheduled_start,
                          "end": lc.scheduled_start + timedelta(minutes=lc.duration_minutes or 45), "editable": False})
        return Response({"items": items, "can": can})


class RecipientsView(APIView):
    """People the current user may message."""

    def get(self, request):
        user = request.user
        q = request.query_params.get("q", "")
        qs = User.objects.filter(is_active=True).exclude(id=user.id)
        if user.role in STUDENT_SIDE:
            qs = qs.filter(role__in=STAFF_ROLES)
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(username__icontains=q))
        return Response([{"id": u.id, "label": f"{u.display_name} — {u.get_role_display()}"} for u in qs.order_by("first_name")[:50]])
