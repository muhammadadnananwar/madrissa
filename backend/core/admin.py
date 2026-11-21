from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("timestamp", "user", "action", "resource", "object_repr", "ip_address")
    list_filter = ("action", "resource")
    search_fields = ("object_repr", "user__username")
    readonly_fields = [f.name for f in AuditLog._meta.fields]
