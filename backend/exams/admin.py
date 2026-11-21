from django.contrib import admin

from .models import (Certificate, Exam, ExamPaper, GradeScale, Mark)


@admin.register(GradeScale)
class GradeScaleAdmin(admin.ModelAdmin):
    list_display = ('name', 'min_percentage', 'max_percentage', 'grade_point', 'is_pass', 'remarks')
    search_fields = ('name', 'remarks')
    list_filter = ('is_pass',)


@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'kind', 'academic_year', 'start_date', 'end_date', 'weightage')
    search_fields = ('name',)
    list_filter = ('kind', 'is_published')
    list_select_related = ('academic_year',)


@admin.register(ExamPaper)
class ExamPaperAdmin(admin.ModelAdmin):
    list_display = ('exam', 'section', 'subject', 'date', 'start_time', 'end_time')
    list_filter = ('marks_locked',)
    list_select_related = ('exam', 'section', 'subject', 'room', 'examiner', 'invigilator')


@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ('paper', 'student', 'marks_obtained', 'is_absent', 'remarks', 'entered_by')
    search_fields = ('remarks',)
    list_filter = ('is_absent',)
    list_select_related = ('paper', 'student', 'entered_by')


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('person', 'kind', 'title', 'serial_no', 'verification_code', 'issue_date')
    search_fields = ('title', 'serial_no', 'verification_code')
    list_filter = ('kind', 'is_revoked')
    list_select_related = ('person', 'issued_by')
