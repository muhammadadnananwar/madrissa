from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from core.roles import ACADEMIC, ALL, R, has_role
from core.scopes import children_qs, teacher_section_ids
from core.viewsets import BaseModelViewSet

from . import serializers as s
from .models import (AcademicYear, ClassLevel, Department, Holiday, Room, Section, Subject, Syllabus, TeacherAssignment,
                     TimeSlot, TimetableEntry, Weekday)

G = "Academics"


class AcademicBase(BaseModelViewSet):
    read_roles = ALL
    write_roles = ACADEMIC
    group = G


class AcademicYearViewSet(AcademicBase):
    queryset = AcademicYear.objects.all()
    serializer_class = s.AcademicYearSerializer
    resource_key = "academic-years"
    icon = "calendar"
    list_fields = ["name", "hijri_name", "start_date", "end_date", "is_current"]


class DepartmentViewSet(AcademicBase):
    queryset = Department.objects.all()
    serializer_class = s.DepartmentSerializer
    resource_key = "departments"
    icon = "building"
    search_fields = ["name", "code"]
    list_fields = ["name", "code", "kind", "head", "is_active"]


class ClassLevelViewSet(AcademicBase):
    queryset = ClassLevel.objects.all()
    serializer_class = s.ClassLevelSerializer
    resource_key = "class-levels"
    label, icon = "Classes / Darjaat", "layers"
    search_fields = ["name"]
    list_fields = ["name", "department", "order", "duration_months"]


class SectionViewSet(AcademicBase):
    queryset = Section.objects.all()
    serializer_class = s.SectionSerializer
    resource_key = "sections"
    label, icon = "Sections / Halaqat", "grid"
    search_fields = ["name", "class_level__name"]
    list_fields = ["class_level", "name", "academic_year", "class_teacher", "shift", "gender", "capacity"]


class SubjectViewSet(AcademicBase):
    queryset = Subject.objects.all()
    serializer_class = s.SubjectSerializer
    resource_key = "subjects"
    label, icon = "Subjects & Kutub", "book"
    search_fields = ["name", "code", "book"]
    list_fields = ["name", "code", "book", "department", "class_level", "total_marks"]


class RoomViewSet(AcademicBase):
    queryset = Room.objects.all()
    serializer_class = s.RoomSerializer
    resource_key = "rooms"
    icon = "door"
    list_fields = ["name", "building", "kind", "capacity"]


class TeacherAssignmentViewSet(AcademicBase):
    queryset = TeacherAssignment.objects.all()
    serializer_class = s.TeacherAssignmentSerializer
    resource_key = "teacher-assignments"
    label, icon = "Teacher Assignments", "link"
    list_fields = ["teacher", "subject", "section", "periods_per_week"]
    menu_roles = ACADEMIC + [R.TEACHER]


class TimeSlotViewSet(AcademicBase):
    queryset = TimeSlot.objects.all()
    serializer_class = s.TimeSlotSerializer
    resource_key = "time-slots"
    label, icon = "Periods / Time Slots", "clock"
    list_fields = ["name", "start_time", "end_time", "order", "is_break"]


class TimetableEntryViewSet(AcademicBase):
    queryset = TimetableEntry.objects.all()
    serializer_class = s.TimetableEntrySerializer
    resource_key = "timetable"
    label, icon = "Timetable Entries", "table"
    list_fields = ["section", "day", "time_slot", "subject", "teacher", "room"]


class HolidayViewSet(AcademicBase):
    queryset = Holiday.objects.all()
    serializer_class = s.HolidaySerializer
    resource_key = "holidays"
    label, icon = "Holidays & Vacations", "sun"
    list_fields = ["title", "kind", "start_date", "end_date"]
    menu_roles = ALL


class SyllabusViewSet(AcademicBase):
    queryset = Syllabus.objects.all()
    serializer_class = s.SyllabusSerializer
    resource_key = "syllabus"
    write_roles = ACADEMIC + [R.TEACHER]
    label, icon = "Syllabus & Lesson Plans", "list"
    list_fields = ["subject", "section", "topic", "planned_date", "completed"]
    menu_roles = ACADEMIC + [R.TEACHER]


# ------------------------------------------------------------------ APIViews
class TimetableGridView(APIView):
    """Weekly grid for ?section=, ?teacher= or the current user."""

    def get(self, request):
        user = request.user
        qs = TimetableEntry.objects.select_related("time_slot", "subject", "teacher", "room", "section", "section__class_level")
        section = request.query_params.get("section")
        teacher = request.query_params.get("teacher")
        if section:
            qs = qs.filter(section_id=section)
        elif teacher:
            qs = qs.filter(teacher_id=teacher)
        elif user.role == R.TEACHER:
            qs = qs.filter(teacher=user)
        elif user.role == R.STUDENT and hasattr(user, "student_profile"):
            qs = qs.filter(section_id=user.student_profile.section_id)
        elif user.role == R.PARENT:
            qs = qs.filter(section_id__in=children_qs(user).values_list("section_id", flat=True))
        else:
            qs = qs.none()
        return Response({
            "days": [{"value": v, "label": l} for v, l in Weekday.choices],
            "slots": [{"id": t.id, "name": t.name, "start": t.start_time.strftime("%H:%M"), "end": t.end_time.strftime("%H:%M"),
                       "is_break": t.is_break} for t in TimeSlot.objects.all()],
            "entries": [{"id": e.id, "day": e.day, "slot": e.time_slot_id, "subject": e.subject.name if e.subject else e.note,
                         "teacher": e.teacher.display_name if e.teacher else "", "room": str(e.room) if e.room else "",
                         "section": str(e.section), "note": e.note} for e in qs],
        })


class MySectionsView(APIView):
    """Sections the user manages (all current sections for academic staff)."""

    def get(self, request):
        user = request.user
        if has_role(user, ACADEMIC + [R.EXAM_CONTROLLER, R.HOSTEL_WARDEN]):
            qs = Section.objects.all()
            year = AcademicYear.current()
            if year and request.query_params.get("all") != "1":
                qs = qs.filter(academic_year=year)
        else:
            qs = Section.objects.filter(id__in=teacher_section_ids(user))
        qs = qs.select_related("class_level", "academic_year")
        return Response([{"id": x.id, "label": str(x), "student_count": x.students.filter(status="active").count()} for x in qs])


class SectionSubjectsView(APIView):
    def get(self, request, section_id):
        section = get_object_or_404(Section.objects.select_related("class_level"), pk=section_id)
        ids = set(TeacherAssignment.objects.filter(section=section).values_list("subject_id", flat=True))
        qs = Subject.objects.filter(Q(id__in=ids) | Q(class_level=section.class_level))
        if request.user.role == R.TEACHER and section.class_teacher_id != request.user.id:
            mine = TeacherAssignment.objects.filter(section=section, teacher=request.user).values_list("subject_id", flat=True)
            qs = qs.filter(id__in=mine)
        return Response([{"id": x.id, "label": str(x), "total_marks": x.total_marks, "pass_marks": x.pass_marks}
                         for x in qs.distinct()])
