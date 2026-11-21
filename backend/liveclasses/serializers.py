from django.conf import settings
from rest_framework import serializers

from core.serializers import LabeledModelSerializer

from .models import LiveClass, LiveClassParticipant


class LiveClassSerializer(LabeledModelSerializer):
    class Meta:
        model = LiveClass
        fields = "__all__"
        read_only_fields = ["meeting_id", "host_url", "status"]
        extra_kwargs = {"teacher": {"required": False}}

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request:
            from .views import can_manage
            if not can_manage(request.user, instance):
                data.pop("host_url", None)  # Zoom start links grant host rights
        return data

    def validate(self, attrs):
        section = attrs.get("section", getattr(self.instance, "section", None))
        course = attrs.get("course", getattr(self.instance, "course", None))
        if not section and not course:
            raise serializers.ValidationError({"section": "Choose a section or a course (or both)."})
        if attrs.get("provider") == "custom" and not attrs.get("join_url", getattr(self.instance, "join_url", "")):
            raise serializers.ValidationError({"join_url": "Provide the meeting link for a custom provider."})
        return attrs


class LiveClassParticipantSerializer(LabeledModelSerializer):
    minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model = LiveClassParticipant
        fields = "__all__"


class EndClassSerializer(serializers.Serializer):
    recording_url = serializers.URLField(required=False, allow_blank=True)


class RecurringScheduleSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=200)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    section = serializers.IntegerField(required=False, allow_null=True)
    course = serializers.IntegerField(required=False, allow_null=True)
    subject = serializers.IntegerField(required=False, allow_null=True)
    teacher = serializers.IntegerField(required=False, allow_null=True)
    provider = serializers.ChoiceField(choices=LiveClass.Provider.choices, default=settings.LIVE_CLASS_DEFAULT_PROVIDER)
    time = serializers.TimeField()
    duration_minutes = serializers.IntegerField(min_value=5, max_value=600, default=45)
    weekdays = serializers.ListField(child=serializers.IntegerField(min_value=0, max_value=6), allow_empty=False)
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    auto_attendance = serializers.BooleanField(default=True)

    def validate(self, attrs):
        if not attrs.get("section") and not attrs.get("course"):
            raise serializers.ValidationError({"section": "Choose a section or a course."})
        if attrs["end_date"] < attrs["start_date"]:
            raise serializers.ValidationError({"end_date": "End date must be after start date."})
        if (attrs["end_date"] - attrs["start_date"]).days > 200:
            raise serializers.ValidationError({"end_date": "Maximum range is 200 days."})
        if attrs["provider"] == "custom":
            raise serializers.ValidationError({"provider": "Recurring classes need an automatic provider."})
        return attrs
