from django.contrib import admin

from .models import (LiveClass, LiveClassParticipant)


@admin.register(LiveClass)
class LiveClassAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'section', 'subject', 'teacher', 'provider')
    search_fields = ('title', 'meeting_id', 'join_url')
    list_filter = ('provider', 'status', 'auto_attendance')
    list_select_related = ('course', 'section', 'subject', 'teacher')


@admin.register(LiveClassParticipant)
class LiveClassParticipantAdmin(admin.ModelAdmin):
    list_display = ('live_class', 'user', 'joined_at', 'left_at', 'join_count')
    list_select_related = ('live_class', 'user')
