from rest_framework import serializers

from core.serializers import LabeledModelSerializer

from .models import LeaveRequest, LeaveType


class LeaveTypeSerializer(LabeledModelSerializer):
    class Meta:
        model = LeaveType
        fields = "__all__"


class LeaveRequestSerializer(LabeledModelSerializer):
    days = serializers.FloatField(read_only=True)

    class Meta:
        model = LeaveRequest
        fields = "__all__"
        read_only_fields = ["status", "reviewed_by", "reviewed_at", "review_remarks"]
        # defaults to the requester; parents / HR choose the person
        extra_kwargs = {"user": {"required": False}}

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and end < start:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})
        return attrs


class ReviewSerializer(serializers.Serializer):
    remarks = serializers.CharField(required=False, allow_blank=True, default="")
