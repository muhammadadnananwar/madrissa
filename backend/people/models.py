import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from academics.models import ClassLevel, Department, Section
from core.models import TimeStamped

User = settings.AUTH_USER_MODEL


class BloodGroup(models.TextChoices):
    A_POS = "A+", "A+"
    A_NEG = "A-", "A-"
    B_POS = "B+", "B+"
    B_NEG = "B-", "B-"
    AB_POS = "AB+", "AB+"
    AB_NEG = "AB-", "AB-"
    O_POS = "O+", "O+"
    O_NEG = "O-", "O-"


class Guardian(TimeStamped):
    class Relation(models.TextChoices):
        FATHER = "father", "Father"
        MOTHER = "mother", "Mother"
        BROTHER = "brother", "Brother"
        UNCLE = "uncle", "Uncle"
        GRANDFATHER = "grandfather", "Grandfather"
        SPONSOR = "sponsor", "Sponsor / Kafeel"
        OTHER = "other", "Other"

    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="guardian_profile",
                                help_text="Portal login of the guardian (role: parent)")
    name = models.CharField(max_length=150)
    relation = models.CharField(max_length=20, choices=Relation.choices, default=Relation.FATHER)
    cnic = models.CharField("CNIC", max_length=30, blank=True)
    phone = models.CharField(max_length=30)
    alt_phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    occupation = models.CharField(max_length=100, blank=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    address = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Student(TimeStamped):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"
        LEFT = "left", "Left / Withdrawn"
        GRADUATED = "graduated", "Graduated (Fazil)"
        TRANSFERRED = "transferred", "Transferred"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    admission_no = models.CharField(max_length=30, unique=True)
    roll_no = models.CharField(max_length=30, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL, related_name="students")
    guardian = models.ForeignKey(Guardian, null=True, blank=True, on_delete=models.SET_NULL, related_name="students")
    second_guardian = models.ForeignKey(Guardian, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    admission_date = models.DateField(default=timezone.localdate)
    leaving_date = models.DateField(null=True, blank=True)
    leaving_reason = models.CharField(max_length=200, blank=True)
    mother_name = models.CharField(max_length=150, blank=True)
    blood_group = models.CharField(max_length=4, choices=BloodGroup.choices, blank=True)
    nationality = models.CharField(max_length=50, default="Pakistani")
    mother_tongue = models.CharField(max_length=50, blank=True)
    previous_institution = models.CharField(max_length=200, blank=True)
    previous_education = models.CharField(max_length=200, blank=True)
    is_boarder = models.BooleanField("Hostel boarder", default=False)
    is_orphan = models.BooleanField("Yateem (orphan)", default=False)
    is_zakat_eligible = models.BooleanField("Zakat / sponsorship eligible", default=False)
    sponsor_name = models.CharField(max_length=150, blank=True)
    emergency_contact = models.CharField(max_length=60, blank=True)
    medical_notes = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["admission_no"]

    def __str__(self):
        return f"{self.user.display_name} [{self.admission_no}]"


class Employee(TimeStamped):
    class Kind(models.TextChoices):
        TEACHING = "teaching", "Teaching (Asatiza)"
        ADMIN = "administrative", "Administrative"
        SUPPORT = "support", "Support Staff"

    class EmploymentType(models.TextChoices):
        PERMANENT = "permanent", "Permanent"
        CONTRACT = "contract", "Contract"
        VISITING = "visiting", "Visiting"
        PART_TIME = "part_time", "Part time"
        VOLUNTEER = "volunteer", "Volunteer (Fi Sabeelillah)"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        ON_LEAVE = "on_leave", "On long leave"
        RESIGNED = "resigned", "Resigned"
        TERMINATED = "terminated", "Terminated"
        RETIRED = "retired", "Retired"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="employee_profile")
    employee_no = models.CharField(max_length=30, unique=True)
    designation = models.CharField(max_length=120, help_text="e.g. Shaykh-ul-Hadith, Ustadh Hifz, Accountant")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.TEACHING)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL, related_name="employees")
    employment_type = models.CharField(max_length=20, choices=EmploymentType.choices, default=EmploymentType.PERMANENT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    joining_date = models.DateField(default=timezone.localdate)
    leaving_date = models.DateField(null=True, blank=True)
    highest_qualification = models.CharField(max_length=200, blank=True, help_text="e.g. Shahadat-ul-Alamiyyah, MA Islamiyat")
    specialization = models.CharField(max_length=200, blank=True, help_text="e.g. Hadith, Fiqh, Tajweed")
    ijazah = models.TextField("Ijazah / Sanad details", blank=True)
    experience_years = models.PositiveIntegerField(default=0)
    basic_salary = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bank_name = models.CharField(max_length=100, blank=True)
    bank_account = models.CharField(max_length=60, blank=True)
    blood_group = models.CharField(max_length=4, choices=BloodGroup.choices, blank=True)
    emergency_contact = models.CharField(max_length=60, blank=True)
    duty_start = models.TimeField(null=True, blank=True, help_text="Expected arrival time (for late marking)")
    duty_end = models.TimeField(null=True, blank=True)
    bio = models.TextField(blank=True)
    show_on_website = models.BooleanField(default=False)
    website_order = models.PositiveIntegerField(default=100)

    class Meta:
        ordering = ["website_order", "employee_no"]

    def __str__(self):
        return f"{self.user.display_name} — {self.designation}"


class Qualification(TimeStamped):
    person = models.ForeignKey(User, on_delete=models.CASCADE, related_name="qualifications")
    title = models.CharField(max_length=200, help_text="Degree / Sanad / Certificate")
    institution = models.CharField(max_length=200)
    year = models.PositiveIntegerField(null=True, blank=True)
    grade = models.CharField(max_length=40, blank=True)
    document = models.FileField(upload_to="people/qualifications/", null=True, blank=True)

    class Meta:
        ordering = ["-year"]

    def __str__(self):
        return f"{self.title} — {self.institution}"


class EmploymentHistory(TimeStamped):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="history")
    organization = models.CharField(max_length=200)
    position = models.CharField(max_length=120)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "employment history"

    def __str__(self):
        return f"{self.position} @ {self.organization}"


class PersonDocument(TimeStamped):
    class Kind(models.TextChoices):
        CNIC = "cnic", "CNIC / B-Form"
        BIRTH = "birth", "Birth certificate"
        PHOTO = "photo", "Photograph"
        CERTIFICATE = "certificate", "Certificate / Degree"
        CONTRACT = "contract", "Contract / Appointment letter"
        MEDICAL = "medical", "Medical"
        LEAVING = "leaving", "School leaving certificate"
        OTHER = "other", "Other"

    person = models.ForeignKey(User, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=150)
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.OTHER)
    file = models.FileField(upload_to="people/documents/")
    expiry_date = models.DateField(null=True, blank=True)
    notes = models.CharField(max_length=255, blank=True)
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    def __str__(self):
        return self.title


class DisciplinaryRecord(TimeStamped):
    class Severity(models.TextChoices):
        MINOR = "minor", "Minor"
        MODERATE = "moderate", "Moderate"
        MAJOR = "major", "Major"

    person = models.ForeignKey(User, on_delete=models.CASCADE, related_name="disciplinary_records")
    date = models.DateField(default=timezone.localdate)
    incident = models.TextField()
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MINOR)
    action_taken = models.TextField(blank=True)
    guardian_informed = models.BooleanField(default=False)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.person.display_name} — {self.date}"


class MedicalRecord(TimeStamped):
    person = models.ForeignKey(User, on_delete=models.CASCADE, related_name="medical_records")
    date = models.DateField(default=timezone.localdate)
    condition = models.CharField(max_length=200)
    treatment = models.TextField(blank=True)
    doctor = models.CharField(max_length=120, blank=True)
    follow_up = models.DateField(null=True, blank=True)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.person.display_name}: {self.condition}"


class Achievement(TimeStamped):
    person = models.ForeignKey(User, on_delete=models.CASCADE, related_name="achievements")
    title = models.CharField(max_length=200)
    date = models.DateField(default=timezone.localdate)
    category = models.CharField(max_length=60, blank=True, help_text="e.g. Qira'at competition, Naat, Debate")
    description = models.TextField(blank=True)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return self.title


class StudentPromotion(TimeStamped):
    class Result(models.TextChoices):
        PROMOTED = "promoted", "Promoted"
        REPEATED = "repeated", "Repeated (detained)"
        GRADUATED = "graduated", "Graduated"

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="promotions")
    from_section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    to_section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    result = models.CharField(max_length=20, choices=Result.choices, default=Result.PROMOTED)
    date = models.DateField(default=timezone.localdate)
    remarks = models.CharField(max_length=200, blank=True)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.student} {self.result}"


def _application_no():
    return f"APP-{timezone.now():%Y}-{secrets.token_hex(3).upper()}"


class AdmissionApplication(TimeStamped):
    class Status(models.TextChoices):
        SUBMITTED = "submitted", "Submitted"
        UNDER_REVIEW = "under_review", "Under review"
        TEST_SCHEDULED = "test_scheduled", "Entry test / interview scheduled"
        DOCUMENTS_REQUIRED = "documents_required", "Documents required"
        ACCEPTED = "accepted", "Accepted"
        WAITLISTED = "waitlisted", "Waitlisted"
        REJECTED = "rejected", "Rejected"
        ENROLLED = "enrolled", "Enrolled"

    application_no = models.CharField(max_length=30, unique=True, default=_application_no, editable=False)
    full_name = models.CharField(max_length=150)
    father_name = models.CharField(max_length=150)
    gender = models.CharField(max_length=10, choices=[("male", "Male"), ("female", "Female")])
    date_of_birth = models.DateField()
    cnic = models.CharField("CNIC / B-Form", max_length=30, blank=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField(blank=True)
    address = models.TextField()
    city = models.CharField(max_length=80, blank=True)
    department = models.ForeignKey(Department, null=True, blank=True, on_delete=models.SET_NULL)
    class_level = models.ForeignKey(ClassLevel, null=True, blank=True, on_delete=models.SET_NULL)
    previous_institution = models.CharField(max_length=200, blank=True)
    previous_education = models.CharField(max_length=200, blank=True)
    quran_status = models.CharField(max_length=120, blank=True, help_text="e.g. Nazra complete, 10 paras memorised")
    guardian_name = models.CharField(max_length=150)
    guardian_relation = models.CharField(max_length=30, default="father")
    guardian_phone = models.CharField(max_length=30)
    guardian_cnic = models.CharField(max_length=30, blank=True)
    guardian_occupation = models.CharField(max_length=100, blank=True)
    needs_hostel = models.BooleanField(default=False)
    requests_scholarship = models.BooleanField(default=False)
    photo = models.ImageField(upload_to="admissions/photos/", null=True, blank=True)
    document = models.FileField(upload_to="admissions/docs/", null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SUBMITTED, db_index=True)
    test_date = models.DateTimeField(null=True, blank=True)
    test_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    remarks = models.TextField(blank=True)
    enrolled_student = models.OneToOneField(Student, null=True, blank=True, on_delete=models.SET_NULL, editable=False)

    # --- Online admission form on the public website ---------------------------------------
    class Residence(models.TextChoices):
        BOARDING = "boarding", "Dar-ul-Iqama (boarding)"
        DAY = "day_scholar", "Day scholar"

    source = models.CharField(max_length=10, choices=[("office", "Office / portal"), ("website", "Website")], default="office")
    program = models.ForeignKey("cms.Program", null=True, blank=True, on_delete=models.SET_NULL, related_name="applications",
                                help_text="Program chosen on the website")
    second_choice = models.ForeignKey("cms.Program", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    session = models.CharField(max_length=40, blank=True)
    shift = models.CharField(max_length=10, blank=True, default="morning")
    darjah = models.CharField("Class / darjah applied for", max_length=80, blank=True)
    residence = models.CharField(max_length=12, choices=Residence.choices, blank=True)
    nationality = models.CharField(max_length=60, blank=True, default="Pakistani")
    province = models.CharField(max_length=60, blank=True)
    temporary_address = models.TextField(blank=True)
    home_phone = models.CharField(max_length=30, blank=True)
    father_cnic = models.CharField(max_length=30, blank=True)
    father_occupation = models.CharField(max_length=100, blank=True)
    education = models.JSONField(default=list, blank=True, help_text="Results: [{level, board, passingYear, totalMarks, obtainedMarks, percentage}]")
    aggregate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,
                                    help_text="Average percentage of the education results (used for merit lists)")
    declaration_accepted = models.BooleanField(default=False)
    rules_accepted = models.BooleanField(default=False)
    status_history = models.JSONField(default=list, blank=True, editable=False)
    submitted_ip = models.GenericIPAddressField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.application_no} — {self.full_name}"

    def compute_aggregate(self):
        pcts = []
        for e in self.education or []:
            try:
                total, got = float(e.get("totalMarks")), float(e.get("obtainedMarks"))
            except (TypeError, ValueError):
                continue
            if total > 0 and 0 <= got <= total:
                e["percentage"] = round(got / total * 100, 2)
                pcts.append(e["percentage"])
        self.aggregate = round(sum(pcts) / len(pcts), 2) if pcts else None

    def save(self, *args, **kwargs):
        # Keep a status timeline for the public "Track application" page.
        previous = None
        if self.pk:
            previous = type(self).objects.filter(pk=self.pk).values_list("status", flat=True).first()
        if previous != self.status:
            self.status_history = [*(self.status_history or []), {
                "status": self.status, "at": timezone.now().isoformat(),
                "remarks": "Application received" if previous is None else ""}]
        super().save(*args, **kwargs)


class AdmissionDocument(TimeStamped):
    """Files uploaded with an online application (photo, CNIC, certificates...). Private: never served publicly."""
    class Kind(models.TextChoices):
        PHOTO = "photo", "Photograph"
        CNIC = "cnic", "Applicant CNIC / B-Form"
        GUARDIAN_CNIC = "guardianCnic", "Father / guardian CNIC"
        CERTIFICATES = "certificates", "Certificates"
        MATRIC = "matric", "Matric"
        INTERMEDIATE = "intermediate", "Intermediate"
        BACHELOR = "bachelor", "Bachelor"
        DOMICILE = "domicile", "Domicile"
        OTHER = "other", "Other"

    application = models.ForeignKey(AdmissionApplication, on_delete=models.CASCADE, related_name="documents")
    kind = models.CharField(max_length=20, choices=Kind.choices)
    file = models.FileField(upload_to="admissions/docs/")
    original_name = models.CharField(max_length=200, blank=True)
    size = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["application", "kind"]

    def __str__(self):
        return f"{self.application.application_no} — {self.get_kind_display()}"


class VisitorLog(TimeStamped):
    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    cnic = models.CharField(max_length=30, blank=True)
    purpose = models.CharField(max_length=200)
    person_to_meet = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="visitors")
    student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.SET_NULL, help_text="If visiting a student")
    check_in = models.DateTimeField(default=timezone.now)
    check_out = models.DateTimeField(null=True, blank=True)
    badge_no = models.CharField(max_length=20, blank=True)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-check_in"]

    def __str__(self):
        return f"{self.name} — {self.check_in:%Y-%m-%d %H:%M}"
