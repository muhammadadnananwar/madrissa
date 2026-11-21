"""Role definitions shared across the whole system."""
from django.db import models


class Role(models.TextChoices):
    SUPER_ADMIN = "super_admin", "Super Admin"
    PRINCIPAL = "principal", "Principal (Mohtamim)"
    ADMIN = "admin", "Administrator (Nazim)"
    ACADEMIC_COORDINATOR = "academic_coordinator", "Academic Coordinator (Nazim-e-Taleemat)"
    TEACHER = "teacher", "Teacher (Ustadh / Ustadha)"
    STUDENT = "student", "Student (Talib / Talibah)"
    PARENT = "parent", "Parent / Guardian"
    ACCOUNTANT = "accountant", "Accountant"
    HR_MANAGER = "hr_manager", "HR Manager"
    ADMISSION_OFFICER = "admission_officer", "Admission Officer"
    EXAM_CONTROLLER = "exam_controller", "Exam Controller"
    LIBRARIAN = "librarian", "Librarian"
    HOSTEL_WARDEN = "hostel_warden", "Hostel Warden"
    TRANSPORT_MANAGER = "transport_manager", "Transport Manager"
    RECEPTIONIST = "receptionist", "Receptionist / Front Desk"
    STORE_KEEPER = "store_keeper", "Store / Inventory Keeper"
    MUFTI = "mufti", "Mufti (Dar-ul-Ifta)"
    MEDIA_MANAGER = "media_manager", "Website / Media Manager"
    STAFF = "staff", "Support Staff"


R = Role
ALL = "*"  # any authenticated user

ADMINS = [R.SUPER_ADMIN, R.PRINCIPAL, R.ADMIN]
ACADEMIC = ADMINS + [R.ACADEMIC_COORDINATOR]
EXAM = ACADEMIC + [R.EXAM_CONTROLLER]
FINANCE = ADMINS + [R.ACCOUNTANT]
HR = ADMINS + [R.HR_MANAGER]
ADMISSION = ADMINS + [R.ADMISSION_OFFICER, R.ACADEMIC_COORDINATOR]
LIBRARY = ADMINS + [R.LIBRARIAN]
HOSTEL = ADMINS + [R.HOSTEL_WARDEN]
TRANSPORT = ADMINS + [R.TRANSPORT_MANAGER]
INVENTORY = ADMINS + [R.STORE_KEEPER]
FRONT_DESK = ADMINS + [R.RECEPTIONIST, R.ADMISSION_OFFICER]
WEBSITE = ADMINS + [R.MEDIA_MANAGER]
IFTA = ADMINS + [R.MUFTI]

STUDENT_SIDE = [R.STUDENT, R.PARENT]
STAFF_ROLES = [r for r in Role.values if r not in STUDENT_SIDE]
# Staff who generally need to look up student records
STUDENT_VIEWERS = ACADEMIC + [
    R.ADMISSION_OFFICER, R.EXAM_CONTROLLER, R.ACCOUNTANT, R.HOSTEL_WARDEN,
    R.TRANSPORT_MANAGER, R.LIBRARIAN, R.RECEPTIONIST, R.HR_MANAGER,
]


def is_admin(user):
    return bool(user and user.is_authenticated and (user.is_superuser or user.role in ADMINS))


def has_role(user, roles):
    if not user or not user.is_authenticated:
        return False
    if roles == ALL or (isinstance(roles, (list, tuple, set)) and ALL in roles):
        return True
    if user.is_superuser or user.role == R.SUPER_ADMIN:
        return True
    return user.role in roles
