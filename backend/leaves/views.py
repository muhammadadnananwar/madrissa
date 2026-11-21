from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from communication.services import notify
from core.audit import audit
from core.roles import ACADEMIC, ALL, HR, R, STUDENT_SIDE, has_role, is_admin
from core.scopes import children_qs, visible_user_ids
from core.viewsets import BaseModelViewSet

from . import serializers as s
from .models import LeaveRequest, LeaveType
from .services import APPROVERS, can_approve, sync_attendance, undo_attendance, used_days

G = "Leaves"


def own_and_family(qs, user):
    return qs.filter(Q(user_id__in=visible_user_ids(user)) | Q(applied_by=user))


def approver_queryset(qs, user):
    if has_role(user, HR):
        return qs
    if has_role(user, ACADEMIC + [R.HOSTEL_WARDEN]):
        return qs.filter(Q(user__role=R.STUDENT) | Q(user=user))
    return own_and_family(qs, user)


class LeaveTypeViewSet(BaseModelViewSet):
    queryset = LeaveType.objects.all()
    serializer_class = s.LeaveTypeSerializer
    resource_key = "leave-types"
    read_roles = ALL
    write_roles = HR + ACADEMIC
    group, icon = G, "tag"
    list_fields = ["name", "code", "applies_to", "days_per_year", "is_paid", "requires_document"]


class LeaveRequestViewSet(BaseModelViewSet):
    queryset = LeaveRequest.objects.all()
    serializer_class = s.LeaveRequestSerializer
    resource_key = "leave-requests"
    write_roles = APPROVERS
    create_roles = ALL
    scope = staticmethod(own_and_family)
    search_fields = ["user__first_name", "user__last_name", "reason"]
    filterset_fields = ["status", "leave_type", "user", "user__role"]
    group, icon, menu = G, "calendar-off", False
    list_fields = ["user", "leave_type", "start_date", "end_date", "status", "applied_by", "reviewed_by"]
    ui_actions = [
        {"name": "approve", "label": "Approve", "style": "success", "roles": APPROVERS,
         "input": [{"name": "remarks", "type": "string", "label": "Remarks"}]},
        {"name": "reject", "label": "Reject", "style": "danger", "roles": APPROVERS,
         "input": [{"name": "remarks", "type": "string", "label": "Reason"}]},
        {"name": "cancel", "label": "Cancel", "roles": ALL, "confirm": "Cancel this leave?"},
    ]

    def get_queryset(self):
        qs = self.base_queryset()
        user = self.request.user
        if is_admin(user):
            return qs
        if user.role in APPROVERS:
            return approver_queryset(qs, user)
        return own_and_family(qs, user)

    def validate_create(self, serializer, extra):
        user = self.request.user
        vd = serializer.validated_data
        target = vd.get("user")
        if user.role == R.PARENT:
            kids = set(children_qs(user).values_list("user_id", flat=True))
            if not target or target.id not in kids:
                raise ValidationError({"user": "Select one of your children."})
        elif not (target and has_role(user, HR + ACADEMIC)):
            extra["user"] = user
        applicant = extra.get("user") or target
        lt = vd["leave_type"]
        kind = "student" if applicant.role in STUDENT_SIDE else "staff"
        if lt.applies_to not in ("both", kind):
            raise ValidationError({"leave_type": f"This leave type is not available for {kind}."})
        if lt.requires_document and not vd.get("document"):
            raise ValidationError({"document": "A supporting document is required for this leave type."})
        if LeaveRequest.objects.filter(user=applicant, status__in=["pending", "approved"],
                                       start_date__lte=vd["end_date"], end_date__gte=vd["start_date"]).exists():
            raise ValidationError({"start_date": "Overlaps with an existing leave request."})
        if lt.days_per_year:
            used = used_days(applicant, lt)
            days = 0.5 if vd.get("half_day") else (vd["end_date"] - vd["start_date"]).days + 1
            if used + days > lt.days_per_year:
                raise ValidationError({"leave_type": f"Insufficient balance: {lt.days_per_year - used} day(s) left."})

    def after_save(self, obj, created):
        if not created:
            return
        approvers = []
        if obj.user.role in STUDENT_SIDE:
            sp = getattr(obj.user, "student_profile", None)
            if sp and sp.section and sp.section.class_teacher:
                approvers.append(sp.section.class_teacher)
        else:
            approvers = list(User.objects.filter(role__in=[R.HR_MANAGER, R.PRINCIPAL], is_active=True))
        notify(approvers, f"Leave request from {obj.user.display_name}",
               f"{obj.leave_type} {obj.start_date} → {obj.end_date}: {obj.reason[:120]}", "/leaves", "leave")

    def _review(self, request, new_status):
        leave = self.get_object()
        if not can_approve(request.user, leave):
            raise PermissionDenied("You cannot review this leave request.")
        if leave.status != LeaveRequest.Status.PENDING:
            return Response({"detail": f"Already {leave.get_status_display().lower()}."}, status=400)
        ser = s.ReviewSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        leave.status = new_status
        leave.reviewed_by = request.user
        leave.reviewed_at = timezone.now()
        leave.review_remarks = ser.validated_data["remarks"]
        leave.save()
        if new_status == LeaveRequest.Status.APPROVED:
            sync_attendance(leave, request.user)
        audit(request, new_status, leave, "leave-requests")
        recipients = [leave.user] + ([leave.applied_by] if leave.applied_by_id and leave.applied_by_id != leave.user_id else [])
        notify(recipients, f"Leave {leave.get_status_display().lower()}",
               f"{leave.leave_type} {leave.start_date} → {leave.end_date}. {leave.review_remarks}", "/leaves", "leave")
        return Response({"detail": f"Leave {leave.get_status_display().lower()}."})

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._review(request, LeaveRequest.Status.APPROVED)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._review(request, LeaveRequest.Status.REJECTED)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        leave = self.get_object()
        mine = request.user.id in (leave.user_id, leave.applied_by_id)
        approver = can_approve(request.user, leave)
        if not (mine or approver):
            raise PermissionDenied()
        if leave.status not in ("pending", "approved"):
            return Response({"detail": "Cannot cancel."}, status=400)
        if leave.status == "approved" and leave.start_date <= timezone.localdate() and not approver:
            return Response({"detail": "Leave already started; ask an approver to cancel."}, status=400)
        was_approved = leave.status == "approved"
        leave.status = LeaveRequest.Status.CANCELLED
        leave.save()
        if was_approved:
            undo_attendance(leave)
        audit(request, "cancel", leave, "leave-requests")
        return Response({"detail": "Leave cancelled."})


class LeaveBalanceView(APIView):
    def get(self, request):
        user = request.user
        target = user
        uid = request.query_params.get("user")
        if uid and int(uid) != user.id:
            if int(uid) not in visible_user_ids(user) and not has_role(user, HR + ACADEMIC):
                raise PermissionDenied()
            target = User.objects.get(pk=uid)
        kind = "student" if target.role in STUDENT_SIDE else "staff"
        out = []
        for lt in LeaveType.objects.filter(applies_to__in=["both", kind]):
            used = used_days(target, lt)
            out.append({"id": lt.id, "name": lt.name, "allowed": lt.days_per_year or None, "used": used,
                        "remaining": (lt.days_per_year - used) if lt.days_per_year else None, "is_paid": lt.is_paid,
                        "requires_document": lt.requires_document})
        return Response({"user": target.id, "name": target.display_name, "types": out})


class PendingLeavesView(APIView):
    """Leave requests the current user can approve."""

    def get(self, request):
        user = request.user
        qs = LeaveRequest.objects.filter(status="pending").select_related("user", "leave_type")
        if not is_admin(user):
            qs = approver_queryset(qs, user) if user.role in APPROVERS else qs.none()
        return Response([{"id": l.id, "user": l.user.display_name, "role": l.user.get_role_display(),
                          "leave_type": str(l.leave_type), "start_date": l.start_date, "end_date": l.end_date, "days": l.days,
                          "reason": l.reason, "document": request.build_absolute_uri(l.document.url) if l.document else None,
                          "created_at": l.created_at} for l in qs if can_approve(user, l)])


class OnLeaveTodayView(APIView):
    def get(self, request):
        if not has_role(request.user, HR + ACADEMIC):
            raise PermissionDenied()
        d = timezone.localdate()
        qs = LeaveRequest.objects.filter(status="approved", start_date__lte=d, end_date__gte=d).select_related(
            "user", "leave_type", "substitute")
        return Response([{"user": l.user.display_name, "role": l.user.get_role_display(), "type": str(l.leave_type),
                          "until": l.end_date, "substitute": l.substitute.display_name if l.substitute else None} for l in qs])
