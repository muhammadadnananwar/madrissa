from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from communication.services import notify
from core.roles import ALL, HOSTEL, R, has_role
from core.scopes import by_student, children_qs
from core.viewsets import BaseModelViewSet

from . import serializers as s
from .models import GatePass, Hostel, HostelAllocation, HostelRoom, MessMenu, RollCall

G = "Hostel"


class HostelBase(BaseModelViewSet):
    read_roles = write_roles = HOSTEL
    group = G


class HostelViewSet(HostelBase):
    queryset = Hostel.objects.all()
    serializer_class = s.HostelSerializer
    resource_key = "hostels"
    icon = "home"
    list_fields = ["name", "gender", "warden", "capacity"]


class HostelRoomViewSet(HostelBase):
    queryset = HostelRoom.objects.all()
    serializer_class = s.HostelRoomSerializer
    resource_key = "hostel-rooms"
    label, icon = "Rooms", "door"
    list_fields = ["hostel", "number", "floor", "capacity"]


class HostelAllocationViewSet(HostelBase):
    queryset = HostelAllocation.objects.all()
    serializer_class = s.HostelAllocationSerializer
    resource_key = "hostel-allocations"
    scope = by_student()
    filterset_fields = ["room", "room__hostel", "is_active", "student"]
    label, icon = "Room Allocations", "bed"
    list_fields = ["student", "room", "bed_no", "from_date", "to_date", "is_active"]
    ui_actions = [{"name": "vacate", "label": "Vacate", "roles": HOSTEL, "confirm": "Vacate this bed?"}]

    def validate_create(self, serializer, extra):
        room = serializer.validated_data["room"]
        if room.occupied >= room.capacity:
            raise ValidationError({"room": "Room is full."})
        HostelAllocation.objects.filter(student=serializer.validated_data["student"], is_active=True).update(
            is_active=False, to_date=timezone.localdate())

    def after_save(self, obj, created):
        if obj.is_active and not obj.student.is_boarder:
            obj.student.is_boarder = True
            obj.student.save(update_fields=["is_boarder"])

    @action(detail=True, methods=["post"])
    def vacate(self, request, pk=None):
        a = self.get_object()
        a.is_active, a.to_date = False, timezone.localdate()
        a.save()
        return Response({"detail": "Room vacated."})


class MessMenuViewSet(HostelBase):
    queryset = MessMenu.objects.all()
    serializer_class = s.MessMenuSerializer
    resource_key = "mess-menu"
    read_roles = ALL
    label, icon, menu_roles = "Mess Menu", "food", HOSTEL + [R.STUDENT, R.PARENT]
    list_fields = ["hostel", "day", "meal", "items"]


class GatePassViewSet(HostelBase):
    queryset = GatePass.objects.all()
    serializer_class = s.GatePassSerializer
    resource_key = "gate-passes"
    read_roles = HOSTEL + [R.RECEPTIONIST]
    create_roles = [R.PARENT, R.STUDENT]
    scope = by_student()
    filterset_fields = ["status", "student"]
    label, icon, menu_roles = "Gate Passes / Outings", "exit", HOSTEL + [R.RECEPTIONIST, R.PARENT, R.STUDENT]
    list_fields = ["student", "reason", "out_time", "expected_return", "escort_name", "status"]
    ui_actions = [
        {"name": "approve", "label": "Approve", "style": "success", "roles": HOSTEL},
        {"name": "reject", "label": "Reject", "style": "danger", "roles": HOSTEL},
        {"name": "check_out", "label": "Mark out", "roles": HOSTEL + [R.RECEPTIONIST]},
        {"name": "check_in", "label": "Mark returned", "roles": HOSTEL + [R.RECEPTIONIST]},
    ]

    def validate_create(self, serializer, extra):
        user = self.request.user
        st = serializer.validated_data["student"]
        if user.role == R.PARENT and not children_qs(user).filter(pk=st.pk).exists():
            raise PermissionDenied("Not your child.")
        if user.role == R.STUDENT and st.user_id != user.id:
            raise PermissionDenied()

    def _transition(self, request, allowed_from, status, **fields):
        gp = self.get_object()
        if gp.status not in allowed_from:
            raise ValidationError({"detail": f"Cannot change a pass that is {gp.get_status_display().lower()}."})
        gp.status = status
        for k, v in fields.items():
            setattr(gp, k, v)
        gp.save()
        st = gp.student
        users = [g.user for g in (st.guardian, st.second_guardian) if g and g.user_id] + [st.user]
        notify(users, f"Gate pass {gp.get_status_display().lower()}: {st.user.display_name}", gp.reason, "/m/gate-passes")
        return Response({"detail": f"Gate pass {gp.get_status_display().lower()}."})

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._transition(request, ["requested"], GatePass.Status.APPROVED, approved_by=request.user)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        return self._transition(request, ["requested"], GatePass.Status.REJECTED, approved_by=request.user)

    @action(detail=True, methods=["post"])
    def check_out(self, request, pk=None):
        return self._transition(request, ["approved"], GatePass.Status.OUT, actual_out=timezone.now())

    @action(detail=True, methods=["post"])
    def check_in(self, request, pk=None):
        return self._transition(request, ["out"], GatePass.Status.RETURNED, actual_return=timezone.now())


class RollCallViewSet(HostelBase):
    queryset = RollCall.objects.all()
    serializer_class = s.RollCallSerializer
    resource_key = "roll-calls"
    scope = by_student()
    filterset_fields = ["date", "student", "is_present"]
    label, icon = "Night Roll Call", "moon"
    list_fields = ["date", "student", "is_present", "remarks"]


class HostelAPIView(APIView):
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not has_role(request.user, HOSTEL):
            raise PermissionDenied()


class RollCallSheetView(HostelAPIView):
    def get(self, request):
        d = request.query_params.get("date") or timezone.localdate().isoformat()
        allocs = HostelAllocation.objects.filter(is_active=True).select_related("student__user", "room")
        if request.query_params.get("hostel"):
            allocs = allocs.filter(room__hostel_id=request.query_params["hostel"])
        existing = {r.student_id: r for r in RollCall.objects.filter(date=d)}
        out_now = set(GatePass.objects.filter(status="out").values_list("student_id", flat=True))
        return Response({"date": d, "rows": [{
            "student": a.student_id, "name": a.student.user.display_name, "room": str(a.room), "bed": a.bed_no,
            "on_gate_pass": a.student_id in out_now,
            "is_present": existing[a.student_id].is_present if a.student_id in existing else None,
            "remarks": existing[a.student_id].remarks if a.student_id in existing else ""} for a in allocs]})

    @transaction.atomic
    def post(self, request):
        ser = s.RollCallSheetSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        for r in d["records"]:
            RollCall.objects.update_or_create(student_id=r["student"], date=d["date"], defaults={
                "is_present": r["is_present"], "remarks": r["remarks"], "recorded_by": request.user})
        return Response({"detail": f"Roll call saved for {len(d['records'])} student(s)."})


class OccupancyView(HostelAPIView):
    def get(self, request):
        out = []
        for h in Hostel.objects.prefetch_related("rooms__allocations__student__user"):
            rooms = []
            for r in h.rooms.all():
                active = [a for a in r.allocations.all() if a.is_active]
                rooms.append({"id": r.id, "number": r.number, "capacity": r.capacity, "occupied": len(active),
                              "students": [str(a.student) for a in active]})
            out.append({"id": h.id, "name": h.name, "capacity": sum(r["capacity"] for r in rooms),
                        "occupied": sum(r["occupied"] for r in rooms), "rooms": rooms})
        return Response(out)
