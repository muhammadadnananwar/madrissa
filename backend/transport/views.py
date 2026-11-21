from core.roles import ALL, R, TRANSPORT
from core.scopes import by_user
from core.viewsets import BaseModelViewSet

from . import serializers as s
from .models import Route, RouteStop, TransportAssignment, Vehicle

G = "Transport"


class VehicleViewSet(BaseModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = s.VehicleSerializer
    resource_key = "vehicles"
    read_roles = write_roles = TRANSPORT
    group, icon = G, "bus"
    list_fields = ["registration_no", "kind", "capacity", "driver_name", "driver_phone", "insurance_expiry", "is_active"]


class RouteViewSet(BaseModelViewSet):
    queryset = Route.objects.all()
    serializer_class = s.RouteSerializer
    resource_key = "routes"
    read_roles, write_roles = ALL, TRANSPORT
    group, icon, menu_roles = G, "map", TRANSPORT + [R.ACCOUNTANT]
    list_fields = ["name", "vehicle", "monthly_fare"]


class RouteStopViewSet(BaseModelViewSet):
    queryset = RouteStop.objects.all()
    serializer_class = s.RouteStopSerializer
    resource_key = "route-stops"
    read_roles, write_roles = ALL, TRANSPORT
    label, group, icon = "Stops", G, "pin"
    list_fields = ["route", "name", "pickup_time", "drop_time", "order"]


class TransportAssignmentViewSet(BaseModelViewSet):
    queryset = TransportAssignment.objects.all()
    serializer_class = s.TransportAssignmentSerializer
    resource_key = "transport-assignments"
    read_roles, write_roles = TRANSPORT + [R.ACCOUNTANT], TRANSPORT
    scope = by_user()
    label, group, icon = "Transport Users", G, "users"
    menu_roles = TRANSPORT + [R.ACCOUNTANT, R.STUDENT, R.PARENT]
    list_fields = ["user", "route", "stop", "from_date", "is_active"]
