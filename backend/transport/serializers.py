from core.serializers import LabeledModelSerializer

from .models import Route, RouteStop, TransportAssignment, Vehicle


class VehicleSerializer(LabeledModelSerializer):
    class Meta:
        model = Vehicle
        fields = "__all__"


class RouteSerializer(LabeledModelSerializer):
    class Meta:
        model = Route
        fields = "__all__"


class RouteStopSerializer(LabeledModelSerializer):
    class Meta:
        model = RouteStop
        fields = "__all__"


class TransportAssignmentSerializer(LabeledModelSerializer):
    class Meta:
        model = TransportAssignment
        fields = "__all__"
