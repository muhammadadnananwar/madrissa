from core.serializers import LabeledModelSerializer

from .models import (AcademicYear, ClassLevel, Department, Holiday, Room, Section, Subject, Syllabus, TeacherAssignment,
                     TimeSlot, TimetableEntry)


class AcademicYearSerializer(LabeledModelSerializer):
    class Meta:
        model = AcademicYear
        fields = "__all__"


class DepartmentSerializer(LabeledModelSerializer):
    class Meta:
        model = Department
        fields = "__all__"


class ClassLevelSerializer(LabeledModelSerializer):
    class Meta:
        model = ClassLevel
        fields = "__all__"


class RoomSerializer(LabeledModelSerializer):
    class Meta:
        model = Room
        fields = "__all__"


class SectionSerializer(LabeledModelSerializer):
    class Meta:
        model = Section
        fields = "__all__"

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["label"] = str(instance)
        return data


class SubjectSerializer(LabeledModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


class TeacherAssignmentSerializer(LabeledModelSerializer):
    class Meta:
        model = TeacherAssignment
        fields = "__all__"


class TimeSlotSerializer(LabeledModelSerializer):
    class Meta:
        model = TimeSlot
        fields = "__all__"


class TimetableEntrySerializer(LabeledModelSerializer):
    class Meta:
        model = TimetableEntry
        fields = "__all__"


class HolidaySerializer(LabeledModelSerializer):
    class Meta:
        model = Holiday
        fields = "__all__"


class SyllabusSerializer(LabeledModelSerializer):
    class Meta:
        model = Syllabus
        fields = "__all__"
