from rest_framework import serializers

from core.serializers import LabeledModelSerializer

from .models import Certificate, Exam, ExamPaper, GradeScale, Mark


class GradeScaleSerializer(LabeledModelSerializer):
    class Meta:
        model = GradeScale
        fields = "__all__"


class ExamSerializer(LabeledModelSerializer):
    class Meta:
        model = Exam
        fields = "__all__"


class ExamPaperSerializer(LabeledModelSerializer):
    class Meta:
        model = ExamPaper
        fields = "__all__"

    def validate(self, attrs):
        mx = attrs.get("max_marks", getattr(self.instance, "max_marks", None))
        ps = attrs.get("pass_marks", getattr(self.instance, "pass_marks", None))
        if mx is not None and ps is not None and ps > mx:
            raise serializers.ValidationError({"pass_marks": "Pass marks cannot exceed max marks."})
        return attrs


class MarkSerializer(LabeledModelSerializer):
    class Meta:
        model = Mark
        fields = "__all__"


class CertificateSerializer(LabeledModelSerializer):
    class Meta:
        model = Certificate
        fields = "__all__"


class MarkEntrySerializer(serializers.Serializer):
    student = serializers.IntegerField()
    marks_obtained = serializers.DecimalField(max_digits=6, decimal_places=2, required=False, allow_null=True, min_value=0)
    is_absent = serializers.BooleanField(default=False)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class MarksSheetSerializer(serializers.Serializer):
    records = MarkEntrySerializer(many=True)
