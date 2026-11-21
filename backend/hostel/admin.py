from django.contrib import admin

from .models import (GatePass, Hostel, HostelAllocation, HostelRoom, MessMenu, RollCall)


@admin.register(Hostel)
class HostelAdmin(admin.ModelAdmin):
    list_display = ('name', 'gender', 'warden', 'address', 'capacity')
    search_fields = ('name', 'address')
    list_filter = ('gender',)
    list_select_related = ('warden',)


@admin.register(HostelRoom)
class HostelRoomAdmin(admin.ModelAdmin):
    list_display = ('hostel', 'number', 'floor', 'capacity', 'notes')
    search_fields = ('number', 'floor', 'notes')
    list_select_related = ('hostel',)


@admin.register(HostelAllocation)
class HostelAllocationAdmin(admin.ModelAdmin):
    list_display = ('student', 'room', 'bed_no', 'from_date', 'to_date', 'is_active')
    search_fields = ('bed_no',)
    list_filter = ('is_active',)
    list_select_related = ('student', 'room')


@admin.register(MessMenu)
class MessMenuAdmin(admin.ModelAdmin):
    list_display = ('hostel', 'day', 'meal', 'items')
    search_fields = ('items',)
    list_filter = ('day', 'meal')
    list_select_related = ('hostel',)


@admin.register(GatePass)
class GatePassAdmin(admin.ModelAdmin):
    list_display = ('student', 'reason', 'out_time', 'expected_return', 'actual_out', 'actual_return')
    search_fields = ('reason', 'escort_name', 'escort_phone')
    list_filter = ('status',)
    list_select_related = ('student', 'applied_by', 'approved_by')


@admin.register(RollCall)
class RollCallAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'is_present', 'remarks', 'recorded_by')
    search_fields = ('remarks',)
    list_filter = ('is_present',)
    list_select_related = ('student', 'recorded_by')
