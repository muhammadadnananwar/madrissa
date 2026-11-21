from django.contrib import admin

from .models import (Achievement, AdmissionApplication, DisciplinaryRecord, Employee, EmploymentHistory, Guardian,
                     MedicalRecord, PersonDocument, Qualification, Student, StudentPromotion, VisitorLog)


@admin.register(Guardian)
class GuardianAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'relation', 'cnic', 'phone', 'alt_phone')
    search_fields = ('name', 'cnic', 'phone')
    list_filter = ('relation',)
    list_select_related = ('user',)


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'admission_no', 'roll_no', 'department', 'section', 'guardian')
    search_fields = ('admission_no', 'roll_no', 'leaving_reason')
    list_filter = ('status', 'blood_group', 'is_boarder', 'is_orphan')
    list_select_related = ('user', 'department', 'section', 'guardian', 'second_guardian')


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_no', 'designation', 'kind', 'department', 'employment_type')
    search_fields = ('employee_no', 'designation', 'highest_qualification')
    list_filter = ('kind', 'employment_type', 'status', 'blood_group')
    list_select_related = ('user', 'department')


@admin.register(Qualification)
class QualificationAdmin(admin.ModelAdmin):
    list_display = ('person', 'title', 'institution', 'year', 'grade', 'document')
    search_fields = ('title', 'institution', 'grade')
    list_select_related = ('person',)


@admin.register(EmploymentHistory)
class EmploymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'organization', 'position', 'from_date', 'to_date')
    search_fields = ('organization', 'position')
    list_select_related = ('employee',)


@admin.register(PersonDocument)
class PersonDocumentAdmin(admin.ModelAdmin):
    list_display = ('person', 'title', 'kind', 'file', 'expiry_date', 'notes')
    search_fields = ('title', 'notes')
    list_filter = ('kind',)
    list_select_related = ('person', 'uploaded_by')


@admin.register(DisciplinaryRecord)
class DisciplinaryRecordAdmin(admin.ModelAdmin):
    list_display = ('person', 'date', 'severity', 'guardian_informed', 'recorded_by')
    list_filter = ('severity', 'guardian_informed')
    list_select_related = ('person', 'recorded_by')


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('person', 'date', 'condition', 'doctor', 'follow_up', 'recorded_by')
    search_fields = ('condition', 'doctor')
    list_select_related = ('person', 'recorded_by')


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ('person', 'title', 'date', 'category', 'recorded_by')
    search_fields = ('title', 'category')
    list_select_related = ('person', 'recorded_by')


@admin.register(StudentPromotion)
class StudentPromotionAdmin(admin.ModelAdmin):
    list_display = ('student', 'from_section', 'to_section', 'result', 'date', 'remarks')
    search_fields = ('remarks',)
    list_filter = ('result',)
    list_select_related = ('student', 'from_section', 'to_section', 'recorded_by')


@admin.register(AdmissionApplication)
class AdmissionApplicationAdmin(admin.ModelAdmin):
    list_display = ('application_no', 'full_name', 'father_name', 'gender', 'date_of_birth', 'cnic')
    search_fields = ('application_no', 'full_name', 'father_name')
    list_filter = ('gender', 'needs_hostel', 'requests_scholarship', 'status')
    list_select_related = ('department', 'class_level', 'enrolled_student')


@admin.register(VisitorLog)
class VisitorLogAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'cnic', 'purpose', 'person_to_meet', 'student')
    search_fields = ('name', 'phone', 'cnic')
    list_select_related = ('person_to_meet', 'student', 'recorded_by')
