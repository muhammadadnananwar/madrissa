from django.contrib import admin

from .models import (Announcement, Complaint, Event, Message, Notification, ParentMeeting)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'priority', 'attachment', 'publish_at', 'expires_at')
    search_fields = ('title',)
    list_filter = ('priority', 'is_pinned', 'notify')
    list_select_related = ('section', 'created_by')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'kind', 'link', 'is_read')
    search_fields = ('title', 'kind', 'link')
    list_filter = ('is_read',)
    list_select_related = ('user',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'attachment', 'reply_to', 'read_at')
    search_fields = ('subject',)
    list_filter = ('deleted_by_sender', 'deleted_by_recipient')
    list_select_related = ('sender', 'recipient', 'reply_to')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'kind', 'start', 'end', 'location')
    search_fields = ('title', 'location')
    list_filter = ('kind', 'is_public')
    list_select_related = ('created_by',)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('submitted_by', 'category', 'subject', 'is_anonymous', 'status', 'assigned_to')
    search_fields = ('subject',)
    list_filter = ('category', 'is_anonymous', 'status')
    list_select_related = ('submitted_by', 'assigned_to')


@admin.register(ParentMeeting)
class ParentMeetingAdmin(admin.ModelAdmin):
    list_display = ('student', 'teacher', 'scheduled_at', 'agenda', 'status', 'created_by')
    search_fields = ('agenda',)
    list_filter = ('status',)
    list_select_related = ('student', 'teacher', 'created_by')
