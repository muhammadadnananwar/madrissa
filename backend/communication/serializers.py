from rest_framework import serializers

from core.roles import Role
from core.serializers import LabeledModelSerializer

from .models import Announcement, Complaint, Event, Message, Notification, ParentMeeting


class AnnouncementSerializer(LabeledModelSerializer):
    class Meta:
        model = Announcement
        fields = "__all__"

    def validate_audience(self, value):
        if not isinstance(value, list) or any(v not in Role.values for v in value):
            raise serializers.ValidationError(f"Must be a list of roles: {', '.join(Role.values)}")
        return value


class NotificationSerializer(LabeledModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"
        read_only_fields = ["user", "title", "body", "kind", "link"]


class MessageSerializer(LabeledModelSerializer):
    class Meta:
        model = Message
        fields = "__all__"
        read_only_fields = ["read_at", "deleted_by_sender", "deleted_by_recipient"]


class EventSerializer(LabeledModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"


class ComplaintSerializer(LabeledModelSerializer):
    class Meta:
        model = Complaint
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if instance.is_anonymous and request and request.user.id != instance.submitted_by_id:
            data["submitted_by"] = None
            data["submitted_by_label"] = "Anonymous"
        return data


class ParentMeetingSerializer(LabeledModelSerializer):
    class Meta:
        model = ParentMeeting
        fields = "__all__"
