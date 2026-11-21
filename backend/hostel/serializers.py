from rest_framework import serializers

from core.serializers import LabeledModelSerializer

from .models import GatePass, Hostel, HostelAllocation, HostelRoom, MessMenu, RollCall


class HostelSerializer(LabeledModelSerializer):
    class Meta:
        model = Hostel
        fields = "__all__"


class HostelRoomSerializer(LabeledModelSerializer):
    occupied = serializers.IntegerField(read_only=True)

    class Meta:
        model = HostelRoom
        fields = "__all__"


class HostelAllocationSerializer(LabeledModelSerializer):
    class Meta:
        model = HostelAllocation
        fields = "__all__"


class MessMenuSerializer(LabeledModelSerializer):
    class Meta:
        model = MessMenu
        fields = "__all__"


class GatePassSerializer(LabeledModelSerializer):
    class Meta:
        model = GatePass
        fields = "__all__"
        read_only_fields = ["status", "actual_out", "actual_return"]

    def validate(self, attrs):
        out = attrs.get("out_time", getattr(self.instance, "out_time", None))
        back = attrs.get("expected_return", getattr(self.instance, "expected_return", None))
        if out and back and back <= out:
            raise serializers.ValidationError({"expected_return": "Must be after the out time."})
        return attrs


class RollCallSerializer(LabeledModelSerializer):
    class Meta:
        model = RollCall
        fields = "__all__"


class RollCallEntrySerializer(serializers.Serializer):
    student = serializers.IntegerField()
    is_present = serializers.BooleanField()
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class RollCallSheetSerializer(serializers.Serializer):
    date = serializers.DateField()
    hostel = serializers.IntegerField(required=False, allow_null=True)
    records = RollCallEntrySerializer(many=True)
