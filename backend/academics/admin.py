from django.contrib import admin

from .models import (AcademicYear, ClassLevel, Department, Holiday, Room, Section, Subject, Syllabus,
                     TeacherAssignment, TimeSlot, TimetableEntry)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'hijri_name', 'start_date', 'end_date', 'is_current')
    search_fields = ('name', 'hijri_name')
    list_filter = ('is_current',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_arabic', 'code', 'kind', 'head', 'is_active')
    search_fields = ('name', 'name_arabic', 'code')
    list_filter = ('kind', 'is_active')
    list_select_related = ('head',)


@admin.register(ClassLevel)
class ClassLevelAdmin(admin.ModelAdmin):
    list_display = ('department', 'name', 'name_arabic', 'order', 'duration_months')
    search_fields = ('name', 'name_arabic')
    list_select_related = ('department',)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'building', 'capacity', 'kind')
    search_fields = ('name', 'building')
    list_filter = ('kind',)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('class_level', 'academic_year', 'name', 'class_teacher', 'room', 'capacity')
    search_fields = ('name',)
    list_filter = ('gender', 'shift')
    list_select_related = ('class_level', 'academic_year', 'class_teacher', 'room')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('department', 'class_level', 'name', 'name_arabic', 'code', 'book')
    search_fields = ('name', 'name_arabic', 'code')
    list_filter = ('is_core',)
    list_select_related = ('department', 'class_level')


@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display = ('section', 'subject', 'teacher', 'periods_per_week')
    list_select_related = ('section', 'subject', 'teacher')


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_time', 'end_time', 'order', 'is_break')
    search_fields = ('name',)
    list_filter = ('is_break',)


@admin.register(TimetableEntry)
class TimetableEntryAdmin(admin.ModelAdmin):
    list_display = ('section', 'day', 'time_slot', 'subject', 'teacher', 'room')
    search_fields = ('note',)
    list_filter = ('day',)
    list_select_related = ('section', 'time_slot', 'subject', 'teacher', 'room')


@admin.register(Holiday)
class HolidayAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'kind')
    search_fields = ('title',)
    list_filter = ('kind',)


@admin.register(Syllabus)
class SyllabusAdmin(admin.ModelAdmin):
    list_display = ('subject', 'section', 'topic', 'planned_date', 'completed', 'completed_on')
    search_fields = ('topic',)
    list_filter = ('completed',)
    list_select_related = ('subject', 'section')
