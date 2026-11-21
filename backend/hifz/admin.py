from django.contrib import admin

from .models import (HifzRecord, JuzProgress)


@admin.register(HifzRecord)
class HifzRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'program', 'teacher', 'sabaq_surah', 'sabaq_from_ayah')
    search_fields = ('sabqi_quantity', 'manzil_juz', 'remarks')
    list_filter = ('program', 'sabaq_surah', 'sabaq_quality', 'sabqi_juz')
    list_select_related = ('student', 'teacher')


@admin.register(JuzProgress)
class JuzProgressAdmin(admin.ModelAdmin):
    list_display = ('student', 'juz', 'status', 'started_on', 'completed_on', 'tested_by')
    search_fields = ('remarks',)
    list_filter = ('juz', 'status')
    list_select_related = ('student', 'tested_by')
