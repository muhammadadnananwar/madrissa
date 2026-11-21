from rest_framework import serializers

from core.serializers import LabeledModelSerializer

from .models import StaffAttendance, Status, StudentAttendance


class StudentAttendanceSerializer(LabeledModelSerializer):
    class Meta:
        model = StudentAttendance
        fields = "__all__"


class StaffAttendanceSerializer(LabeledModelSerializer):
    hours_worked = serializers.FloatField(read_only=True)

    class Meta:
        model = StaffAttendance
        fields = "__all__"


class StudentMarkSerializer(serializers.Serializer):
    student = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Status.choices)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class BulkMarkSerializer(serializers.Serializer):
    section = serializers.IntegerField()
    date = serializers.DateField()
    subject = serializers.IntegerField(required=False, allow_null=True)
    time_slot = serializers.IntegerField(required=False, allow_null=True)
    records = StudentMarkSerializer(many=True)


class StaffMarkSerializer(serializers.Serializer):
    employee = serializers.IntegerField()
    status = serializers.ChoiceField(choices=Status.choices)
    check_in = serializers.TimeField(required=False, allow_null=True)
    check_out = serializers.TimeField(required=False, allow_null=True)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class StaffBulkSerializer(serializers.Serializer):
    date = serializers.DateField()
    records = StaffMarkSerializer(many=True)


class SelfCheckSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["check_in", "check_out"])
    location = serializers.CharField(required=False, allow_blank=True, default="", max_length=80)


# ------------------------------------------------------------- biometrics
from .models import BiometricDevice, BiometricEnrollment, BiometricPunch  # noqa: E402


class BiometricDeviceSerializer(LabeledModelSerializer):
    class Meta:
        model = BiometricDevice
        fields = "__all__"
        read_only_fields = ["api_key", "last_seen", "last_punch_at"]


class BiometricEnrollmentSerializer(LabeledModelSerializer):
    class Meta:
        model = BiometricEnrollment
        fields = "__all__"


class BiometricPunchSerializer(LabeledModelSerializer):
    class Meta:
        model = BiometricPunch
        fields = "__all__"


class PunchInSerializer(serializers.Serializer):
    pin = serializers.CharField(max_length=20)
    time = serializers.CharField()
    direction = serializers.CharField(required=False, allow_blank=True, default="")
    verify = serializers.CharField(required=False, allow_blank=True, default="")


class PunchBatchSerializer(serializers.Serializer):
    punches = PunchInSerializer(many=True, allow_empty=False)


class BiometricImportSerializer(serializers.Serializer):
    file = serializers.FileField()
    device = serializers.PrimaryKeyRelatedField(queryset=BiometricDevice.objects.all(), required=False, allow_null=True)


class DateSerializer(serializers.Serializer):
    date = serializers.DateField()
    staff = serializers.BooleanField(default=True)
    students = serializers.BooleanField(default=False)
    include_applied = serializers.BooleanField(default=False)


class AutoEnrollSerializer(serializers.Serializer):
    who = serializers.ChoiceField(choices=["all", "staff", "students"], default="all")
    scheme = serializers.ChoiceField(choices=["id", "number"], default="id")
