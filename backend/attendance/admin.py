from django.contrib import admin

from .models import (StaffAttendance, StudentAttendance)


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'section', 'date', 'subject', 'time_slot', 'status')
    search_fields = ('remarks',)
    list_filter = ('status', 'source', 'guardian_notified')
    list_select_related = ('student', 'section', 'subject', 'time_slot', 'marked_by')


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status', 'check_in', 'check_out', 'source')
    search_fields = ('check_in_location', 'remarks')
    list_filter = ('status', 'source')
    list_select_related = ('employee', 'marked_by')
