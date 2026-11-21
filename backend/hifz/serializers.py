from rest_framework import serializers

from core.serializers import LabeledModelSerializer

from .models import (ChecklistItem, HifzRecord, JuzProgress, ParaProgram, Program, QaidaLesson, QaidaProgress, Quality,
                     QuranCompletion, StudentChecklist, TarjumaProgress)
from .quran import JUZ_CHOICES, SURAH_CHOICES


class HifzRecordSerializer(LabeledModelSerializer):
    class Meta:
        model = HifzRecord
        fields = "__all__"


class JuzProgressSerializer(LabeledModelSerializer):
    class Meta:
        model = JuzProgress
        fields = "__all__"


class DailyEntrySerializer(serializers.Serializer):
    student = serializers.IntegerField()
    sabaq_surah = serializers.ChoiceField(choices=SURAH_CHOICES, required=False, allow_null=True)
    sabaq_from_ayah = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    sabaq_to_ayah = serializers.IntegerField(required=False, allow_null=True, min_value=1)
    sabaq_lines = serializers.IntegerField(required=False, default=0, min_value=0)
    sabaq_quality = serializers.ChoiceField(choices=Quality.choices, required=False, allow_blank=True, default="")
    sabqi_juz = serializers.ChoiceField(choices=JUZ_CHOICES, required=False, allow_null=True)
    sabqi_quantity = serializers.CharField(required=False, allow_blank=True, default="")
    sabqi_quality = serializers.ChoiceField(choices=Quality.choices, required=False, allow_blank=True, default="")
    manzil_juz = serializers.CharField(required=False, allow_blank=True, default="")
    manzil_quality = serializers.ChoiceField(choices=Quality.choices, required=False, allow_blank=True, default="")
    mistakes = serializers.IntegerField(required=False, default=0, min_value=0)
    hesitations = serializers.IntegerField(required=False, default=0, min_value=0)
    tajweed_rating = serializers.IntegerField(required=False, default=0, min_value=0, max_value=10)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class DailySheetSerializer(serializers.Serializer):
    section = serializers.IntegerField()
    date = serializers.DateField()
    program = serializers.ChoiceField(choices=Program.choices, default=Program.HIFZ)
    records = DailyEntrySerializer(many=True)


class SetJuzSerializer(serializers.Serializer):
    program = serializers.ChoiceField(choices=ParaProgram.choices, default=ParaProgram.HIFZ)
    juz = serializers.IntegerField(min_value=1, max_value=30)
    status = serializers.ChoiceField(choices=JuzProgress.Status.choices)
    test_score = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100)


class QaidaLessonSerializer(LabeledModelSerializer):
    class Meta:
        model = QaidaLesson
        fields = "__all__"


class QaidaProgressSerializer(LabeledModelSerializer):
    class Meta:
        model = QaidaProgress
        fields = "__all__"


class TarjumaProgressSerializer(LabeledModelSerializer):
    class Meta:
        model = TarjumaProgress
        fields = "__all__"


class QuranCompletionSerializer(LabeledModelSerializer):
    class Meta:
        model = QuranCompletion
        fields = "__all__"


class ChecklistItemSerializer(LabeledModelSerializer):
    class Meta:
        model = ChecklistItem
        fields = "__all__"


class StudentChecklistSerializer(LabeledModelSerializer):
    class Meta:
        model = StudentChecklist
        fields = "__all__"


class SetQaidaSerializer(serializers.Serializer):
    lesson = serializers.PrimaryKeyRelatedField(queryset=QaidaLesson.objects.all())
    status = serializers.ChoiceField(choices=[("not_started", "Not started"), *QaidaProgress.Status.choices])
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class SetTarjumaSerializer(serializers.Serializer):
    surah = serializers.ChoiceField(choices=SURAH_CHOICES)
    status = serializers.ChoiceField(choices=[("not_started", "Not started"), *TarjumaProgress.Status.choices])
    ayahs_done = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    test_score = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=100)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class SetChecklistSerializer(serializers.Serializer):
    item = serializers.PrimaryKeyRelatedField(queryset=ChecklistItem.objects.all())
    status = serializers.ChoiceField(choices=[("not_started", "Not started"), *StudentChecklist.Status.choices])
    score = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=10)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class ChecklistEntrySerializer(serializers.Serializer):
    student = serializers.IntegerField()
    status = serializers.ChoiceField(choices=[("not_started", "Not started"), *StudentChecklist.Status.choices])
    score = serializers.IntegerField(required=False, allow_null=True, min_value=0, max_value=10)


class ChecklistSheetSerializer(serializers.Serializer):
    section = serializers.IntegerField()
    item = serializers.PrimaryKeyRelatedField(queryset=ChecklistItem.objects.all())
    records = ChecklistEntrySerializer(many=True)


class RecordKhatmSerializer(serializers.Serializer):
    kind = serializers.ChoiceField(choices=QuranCompletion.Kind.choices)
    completed_on = serializers.DateField(required=False)
    started_on = serializers.DateField(required=False, allow_null=True)
    remarks = serializers.CharField(required=False, allow_blank=True, default="")
