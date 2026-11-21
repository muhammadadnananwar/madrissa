from django.contrib import admin

from .models import (LeaveRequest, LeaveType)


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'applies_to', 'days_per_year', 'is_paid', 'requires_document')
    search_fields = ('name', 'code')
    list_filter = ('applies_to', 'is_paid', 'requires_document')


@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'applied_by', 'leave_type', 'start_date', 'end_date', 'half_day')
    search_fields = ('review_remarks',)
    list_filter = ('half_day', 'status')
    list_select_related = ('user', 'applied_by', 'leave_type', 'substitute', 'reviewed_by')
