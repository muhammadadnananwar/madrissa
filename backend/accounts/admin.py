from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class MadrasaUserAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "role", "phone", "is_active")
    list_filter = ("role", "is_active", "gender")
    fieldsets = UserAdmin.fieldsets + (
        ("Madrasa profile", {"fields": ("role", "phone", "whatsapp", "cnic", "gender", "date_of_birth",
                                        "father_name", "address", "city", "photo", "name_arabic",
                                        "must_change_password")}),
    )
