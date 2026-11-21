from django.contrib import admin

from .models import (Route, RouteStop, TransportAssignment, Vehicle)


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('registration_no', 'kind', 'capacity', 'driver_name', 'driver_phone', 'driver_license')
    search_fields = ('registration_no', 'kind', 'driver_name')
    list_filter = ('is_active',)


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('name', 'vehicle', 'monthly_fare')
    search_fields = ('name',)
    list_select_related = ('vehicle',)


@admin.register(RouteStop)
class RouteStopAdmin(admin.ModelAdmin):
    list_display = ('route', 'name', 'pickup_time', 'drop_time', 'order')
    search_fields = ('name',)
    list_select_related = ('route',)


@admin.register(TransportAssignment)
class TransportAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'route', 'stop', 'from_date', 'is_active')
    list_filter = ('is_active',)
    list_select_related = ('user', 'route', 'stop')
