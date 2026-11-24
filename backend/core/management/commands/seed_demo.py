"""
Populate the database with realistic demo data for every module and role.

    python manage.py seed_demo            # idempotent-ish: skips if data exists
    python manage.py seed_demo --flush    # wipe and recreate

Demo logins (password: madrasa123, super admin: admin / admin123) are printed at the end.
"""
import random
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from core.roles import R

PASSWORD = "madrasa123"
TEACHERS = [
    ("mufti.abdullah", "Abdullah", "Qasmi", "Shaykh-ul-Hadith", "Hadith & Fiqh", "Takhassus fil Ifta, Jamia Darul Uloom Karachi"),
    ("qari.yusuf", "Yusuf", "Siddiqui", "Head of Hifz", "Hifz & Tajweed", "Qira'at Sab'ah, Ijazah with sanad"),
    ("ustadh.imran", "Imran", "Haider", "Ustadh — Arabic Grammar", "Nahw & Sarf", "Shahadat-ul-Alamiyyah (Wifaq)"),
    ("ustadh.bilal", "Bilal", "Ahmed", "Ustadh — Nazra", "Nazra & Qaida", "Hafiz, Qari"),
    ("ustadha.maryam", "Maryam", "Khan", "Ustadha — Alimah Course", "Tafseer & Seerah", "Alimah, MA Islamiyat"),
    ("sir.kamran", "Kamran", "Ali", "Teacher — Modern Education", "Mathematics & English", "MSc Mathematics"),
]
STAFF = [
    ("principal", R.PRINCIPAL, "Muhammad", "Rafiq", "Mohtamim (Principal)"),
    ("nazim", R.ADMIN, "Ahmad", "Saeed", "Nazim (Administrator)"),
    ("coordinator", R.ACADEMIC_COORDINATOR, "Hamza", "Usmani", "Nazim-e-Taleemat"),
    ("accountant", R.ACCOUNTANT, "Tariq", "Mehmood", "Accountant"),
    ("hr", R.HR_MANAGER, "Saad", "Rehman", "HR Manager"),
    ("admissions", R.ADMISSION_OFFICER, "Zubair", "Hassan", "Admission Officer"),
    ("exams", R.EXAM_CONTROLLER, "Usman", "Ghani", "Exam Controller"),
    ("librarian", R.LIBRARIAN, "Hafiz", "Naeem", "Librarian"),
    ("warden", R.HOSTEL_WARDEN, "Khalid", "Mahmood", "Hostel Warden"),
    ("transport", R.TRANSPORT_MANAGER, "Asif", "Iqbal", "Transport Manager"),
    ("reception", R.RECEPTIONIST, "Faisal", "Nadeem", "Receptionist"),
    ("store", R.STORE_KEEPER, "Rashid", "Latif", "Store Keeper"),
    ("mufti", R.MUFTI, "Mufti Ismail", "Patel", "Mufti, Dar-ul-Ifta"),
    ("media", R.MEDIA_MANAGER, "Owais", "Raza", "Media Manager"),
    ("staff", R.STAFF, "Ghulam", "Nabi", "Caretaker"),
]
BOYS = ["Abdur Rahman", "Ibrahim", "Ismail", "Zakariya", "Musa", "Haroon", "Talha", "Zaid", "Umar", "Ali", "Hasan",
        "Husain", "Saad", "Anas", "Muaz", "Huzaifa", "Ammar", "Khubaib", "Salman", "Yahya"]
GIRLS = ["Aisha", "Fatimah", "Khadijah", "Zainab", "Ruqayyah", "Sumayyah", "Hafsa", "Safiyyah"]
SURNAMES = ["Khan", "Qureshi", "Ansari", "Siddiqui", "Farooqi", "Chaudhry", "Shah", "Malik", "Butt", "Mirza"]


class Command(BaseCommand):
    help = "Seed demo data for the Madrasa Management System"

    def add_arguments(self, parser):
        parser.add_argument("--flush", action="store_true", help="Delete all data first")

    def handle(self, *args, **opts):
        if opts["flush"]:
            call_command("flush", interactive=False)
        if User.objects.filter(username="admin").exists():
            self.stdout.write(self.style.WARNING("Demo data already present (use --flush to recreate)."))
            return
        random.seed(7)
        from attendance.rules import muted
        # Demo attendance is random: don't let it strike students off or warn staff
        with transaction.atomic(), muted():
            self.today = timezone.localdate()
            self.reference_data()
            self.site()
            self.academics()
            self.people()
            self.timetable()
            self.attendance_and_leaves()
            self.exams()
            self.hifz()
            self.quran_programs()
            self.biometrics()
            self.lms()
            self.finance()
            self.library_hostel_transport_inventory()
            self.communication()
            self.website()
        # Public website content (University of Muhammadia Saifia) — runs after the transaction above
        call_command("seed_website", reset=True)
        self.stdout.write(self.style.SUCCESS("Demo data created.\n"))
        self.stdout.write("Super admin: admin / admin123")
        self.stdout.write(f"All other demo users use password: {PASSWORD}")
        for u in User.objects.exclude(username="admin").order_by("role", "username")[:60]:
            self.stdout.write(f"  {u.get_role_display():38} {u.username}")

    # ------------------------------------------------------------------ helpers
    def user(self, username, role, first, last="", **extra):
        u = User(username=username, role=role, first_name=first, last_name=last, email=f"{username}@madrasa.local", **extra)
        u.set_password(PASSWORD)
        u.save()
        return u

    def reference_data(self):
        """Qaida lessons & checklists normally come from a data migration; `flush` removes them."""
        import importlib

        from django.apps import apps as django_apps
        importlib.import_module("hifz.migrations.0003_quran_reference_data").forwards(django_apps, None)

    # --------------------------------------------------------------------- site
    def site(self):
        from website.models import SiteSettings
        SiteSettings.objects.all().delete()
        SiteSettings.objects.create(
            name="University of Muhammadia Saifia", name_arabic="یونیورسٹی آف محمدیہ سیفیہ",
            tagline="Preserving the Qur'an, nurturing scholars, serving the Ummah since 1978",
            founded_year=1978, affiliation="Wifaq-ul-Madaris Al-Arabia Pakistan", registration_no="WMA-1978-0421",
            address="Main University Road, Gulshan-e-Iqbal", city="Karachi", phone="+92 21 3456 7890",
            whatsapp="+92 300 1234567", email="info@muhammadiasaifia.example",
            map_embed_url="https://www.google.com/maps?q=Karachi&output=embed",
            facebook="https://facebook.com/", youtube="https://youtube.com/",
            about_short="A residential and day madrasa offering Hifz-ul-Quran, Nazra, Tajweed, the eight-year "
                        "Dars-e-Nizami Alim course, an Alimah course for girls, and Takhassus fil Ifta, alongside "
                        "matric-level modern education.",
            donation_bank_details="Meezan Bank — Title: University of Muhammadia Saifia\nIBAN: PK00 MEZN 0000 0000 0000 0000\n"
                                  "Zakat account: PK00 MEZN 1111 1111 1111 1111\nJazzCash / Easypaisa: 0300 1234567",
            late_fee_per_invoice=Decimal("200"), library_fine_per_day=Decimal("10"))

        u = User(username="admin", role=R.SUPER_ADMIN, first_name="System", last_name="Administrator",
                 email="admin@madrasa.local", is_staff=True, is_superuser=True)
        u.set_password("admin123")
        u.save()

    # ---------------------------------------------------------------- academics
    def academics(self):
        from academics.models import AcademicYear, ClassLevel, Department, Room, Section, Subject, TimeSlot
        y = self.today.year if self.today.month >= 4 else self.today.year - 1
        self.year = AcademicYear.objects.create(name=f"{y}-{y + 1}", hijri_name="1448-1449 AH",
                                                start_date=date(y, 4, 1), end_date=date(y + 1, 3, 31), is_current=True)
        D = Department.objects.create
        self.dept = {
            "hifz": D(name="Hifz-ul-Quran", name_arabic="تحفيظ القرآن", code="HFZ", kind="hifz"),
            "nazra": D(name="Nazra & Qaida", name_arabic="ناظرة", code="NZR", kind="nazra"),
            "dars": D(name="Dars-e-Nizami (Alim Course)", name_arabic="درس نظامي", code="DRS", kind="dars_e_nizami"),
            "alima": D(name="Alimah Course (Banaat)", name_arabic="عالمة", code="ALM", kind="alima"),
            "tajweed": D(name="Tajweed & Qira'at", name_arabic="تجويد", code="TJW", kind="tajweed"),
            "ifta": D(name="Takhassus fil Ifta", name_arabic="تخصص في الإفتاء", code="IFT", kind="ifta"),
            "modern": D(name="Modern Education (Asri Uloom)", code="MOD", kind="modern"),
            "tarjuma": D(name="Tarjuma-tul-Quran", name_arabic="ترجمة القرآن", code="TRJ", kind="tarjuma"),
        }
        rooms = [Room.objects.create(name=f"Room {i}", building="Main Block", capacity=35) for i in range(1, 9)]
        Room.objects.create(name="Jamia Masjid", kind="masjid", capacity=800)
        Room.objects.create(name="Computer Lab", kind="lab", capacity=25)
        CL = ClassLevel.objects.create
        self.levels = {
            "hifz": CL(department=self.dept["hifz"], name="Hifz Class", order=1, duration_months=36),
            "nazra": CL(department=self.dept["nazra"], name="Nazra Class", order=1, duration_months=18),
            "oola": CL(department=self.dept["dars"], name="Darja Oola", name_arabic="الدرجة الأولى", order=1),
            "saniya": CL(department=self.dept["dars"], name="Darja Saniya", name_arabic="الدرجة الثانية", order=2),
            "alima1": CL(department=self.dept["alima"], name="Alimah Year 1", order=1),
            "grade8": CL(department=self.dept["modern"], name="Grade 8", order=8),
        }
        self.timeslots = [
            TimeSlot.objects.create(name="Period 1", start_time=time(7, 30), end_time=time(8, 15), order=1),
            TimeSlot.objects.create(name="Period 2", start_time=time(8, 15), end_time=time(9, 0), order=2),
            TimeSlot.objects.create(name="Period 3", start_time=time(9, 0), end_time=time(9, 45), order=3),
            TimeSlot.objects.create(name="Break / Chai", start_time=time(9, 45), end_time=time(10, 15), order=4, is_break=True),
            TimeSlot.objects.create(name="Period 4", start_time=time(10, 15), end_time=time(11, 0), order=5),
            TimeSlot.objects.create(name="Period 5", start_time=time(11, 0), end_time=time(11, 45), order=6),
        ]
        self.rooms = rooms
        S = Subject.objects.create
        dars, oola = self.dept["dars"], self.levels["oola"]
        self.subjects = {
            "nahw": S(department=dars, class_level=oola, name="Nahw (Arabic Syntax)", name_arabic="النحو", code="NHW1", book="Hidayat-un-Nahw"),
            "sarf": S(department=dars, class_level=oola, name="Sarf (Morphology)", name_arabic="الصرف", code="SRF1", book="Ilm-us-Sigha"),
            "fiqh": S(department=dars, class_level=oola, name="Fiqh", name_arabic="الفقه", code="FQH1", book="Mukhtasar al-Quduri"),
            "hadith": S(department=dars, class_level=oola, name="Hadith", name_arabic="الحديث", code="HDT1", book="Riyad-us-Saliheen"),
            "arabic": S(department=dars, class_level=oola, name="Arabic Literature", name_arabic="الأدب", code="ADB1", book="Al-Qira'at al-Wadiha"),
            "tafseer": S(department=self.dept["alima"], class_level=self.levels["alima1"], name="Tafseer", code="TFS1", book="Tafseer Jalalayn"),
            "tarjuma": S(department=self.dept["alima"], class_level=self.levels["alima1"], name="Tarjuma-tul-Quran", name_arabic="ترجمة القرآن", code="TRJ1", book="Word-by-word Tarjuma"),
            "hifz": S(department=self.dept["hifz"], class_level=self.levels["hifz"], name="Hifz", code="HFZ1"),
            "nazra": S(department=self.dept["nazra"], class_level=self.levels["nazra"], name="Nazra Quran", code="NZR1"),
            "math": S(department=self.dept["modern"], class_level=self.levels["grade8"], name="Mathematics", code="MTH8"),
            "english": S(department=self.dept["modern"], class_level=self.levels["grade8"], name="English", code="ENG8"),
        }
        self.Section = Section

    # ------------------------------------------------------------------- people
    def people(self):
        from academics.models import TeacherAssignment
        from people.models import Employee, Guardian, Qualification, Student
        self.staff = {}
        n = 1
        for username, role, first, last, desig in STAFF:
            u = self.user(username, role, first, last, phone=f"0300{n:07d}", gender="male")
            Employee.objects.create(user=u, employee_no=f"EMP-{n:03d}", designation=desig, kind="administrative",
                                    basic_salary=Decimal(random.choice([45000, 55000, 65000, 80000])),
                                    joining_date=date(2015 + n % 8, 1 + n % 12, 1), duty_start=time(7, 30), duty_end=time(14, 0),
                                    show_on_website=role in (R.PRINCIPAL, R.MUFTI), website_order=n)
            self.staff[role] = u
            n += 1
        self.teachers = []
        depts = ["dars", "hifz", "dars", "nazra", "alima", "modern"]
        for i, (username, first, last, desig, spec, qual) in enumerate(TEACHERS):
            gender = "female" if username.startswith("ustadha") else "male"
            u = self.user(username, R.TEACHER, first, last, phone=f"0321{i:07d}", gender=gender,
                          name_arabic="", father_name=random.choice(BOYS))
            Employee.objects.create(user=u, employee_no=f"TCH-{i + 1:03d}", designation=desig, kind="teaching",
                                    department=self.dept[depts[i]], specialization=spec, highest_qualification=qual,
                                    experience_years=5 + i * 3, basic_salary=Decimal(50000 + i * 7000),
                                    duty_start=time(7, 15), duty_end=time(13, 30), show_on_website=True, website_order=10 + i,
                                    bio=f"{first} {last} teaches {spec} and has served the University for {5 + i * 3} years.",
                                    ijazah=qual)
            Qualification.objects.create(person=u, title=qual, institution="Wifaq-ul-Madaris", year=2005 + i)
            self.teachers.append(u)
        t = self.teachers
        Sec = self.Section
        self.sections = {
            "hifz": Sec.objects.create(class_level=self.levels["hifz"], academic_year=self.year, name="Halqa A", class_teacher=t[1], room=self.rooms[0]),
            "nazra": Sec.objects.create(class_level=self.levels["nazra"], academic_year=self.year, name="Halqa B", class_teacher=t[3], room=self.rooms[1]),
            "oola": Sec.objects.create(class_level=self.levels["oola"], academic_year=self.year, name="A", class_teacher=t[2], room=self.rooms[2]),
            "alima": Sec.objects.create(class_level=self.levels["alima1"], academic_year=self.year, name="A", class_teacher=t[4],
                                        room=self.rooms[3], gender="female"),
            "grade8": Sec.objects.create(class_level=self.levels["grade8"], academic_year=self.year, name="A", class_teacher=t[5],
                                         room=self.rooms[4], shift="evening"),
        }
        sub = self.subjects
        TA = TeacherAssignment.objects.create
        for subj, teacher in [("nahw", t[2]), ("sarf", t[2]), ("fiqh", t[0]), ("hadith", t[0]), ("arabic", t[2])]:
            TA(section=self.sections["oola"], subject=sub[subj], teacher=teacher)
        TA(section=self.sections["hifz"], subject=sub["hifz"], teacher=t[1])
        TA(section=self.sections["nazra"], subject=sub["nazra"], teacher=t[3])
        TA(section=self.sections["alima"], subject=sub["tafseer"], teacher=t[4])
        TA(section=self.sections["grade8"], subject=sub["math"], teacher=t[5])
        TA(section=self.sections["grade8"], subject=sub["english"], teacher=t[5])

        self.students = []
        self.parents = []
        plan = [("hifz", 6, "male"), ("nazra", 4, "male"), ("oola", 6, "male"), ("alima", 4, "female"), ("grade8", 4, "male")]
        idx = 0
        for key, count, gender in plan:
            for _ in range(count):
                idx += 1
                first = (GIRLS if gender == "female" else BOYS)[idx % (8 if gender == "female" else 20)]
                surname = SURNAMES[idx % len(SURNAMES)]
                father = f"{random.choice(BOYS)} {surname}"
                guardian = None
                if idx <= 10:  # first 10 students have parent logins
                    pu = self.user(f"parent{idx}", R.PARENT, father.split()[0], surname, phone=f"0333{idx:07d}", gender="male")
                    guardian = Guardian.objects.create(user=pu, name=father, relation="father", phone=pu.phone,
                                                       occupation=random.choice(["Shopkeeper", "Engineer", "Teacher", "Driver"]))
                    self.parents.append(pu)
                else:
                    guardian = Guardian.objects.create(name=father, relation="father", phone=f"0345{idx:07d}")
                su = self.user(f"student{idx}", R.STUDENT, first, surname, gender=gender, father_name=father,
                               date_of_birth=date(2010 + idx % 6, 1 + idx % 12, 1 + idx % 27), phone=f"0312{idx:07d}")
                st = Student.objects.create(user=su, admission_no=f"{self.year.start_date.year}-{idx:04d}", roll_no=str(idx),
                                            department=self.sections[key].class_level.department, section=self.sections[key],
                                            guardian=guardian, is_boarder=idx % 3 == 0, is_orphan=idx in (4, 13),
                                            is_zakat_eligible=idx in (4, 7, 13), admission_date=self.year.start_date,
                                            blood_group=random.choice(["A+", "B+", "O+", "AB+"]))
                self.students.append(st)
        # a second child for parent1 (siblings)
        self.students[11].guardian = self.students[0].guardian
        self.students[11].save()

    # ---------------------------------------------------------------- timetable
    def timetable(self):
        from academics.models import TimetableEntry
        oola = self.sections["oola"]
        plan = ["nahw", "sarf", "fiqh", None, "hadith", "arabic"]
        teachers = {"nahw": self.teachers[2], "sarf": self.teachers[2], "fiqh": self.teachers[0],
                    "hadith": self.teachers[0], "arabic": self.teachers[2]}
        for day in range(6):
            for slot, subj in zip(self.timeslots, plan):
                if subj is None:
                    TimetableEntry.objects.create(section=oola, day=day, time_slot=slot, note="Break")
                    continue
                rot = plan[(plan.index(subj) + day) % len(plan)] or subj
                TimetableEntry.objects.create(section=oola, day=day, time_slot=slot, subject=self.subjects[rot],
                                              teacher=teachers[rot], room=self.rooms[2])
            for slot in self.timeslots[:3]:
                TimetableEntry.objects.create(section=self.sections["hifz"], day=day, time_slot=slot,
                                              subject=self.subjects["hifz"], teacher=self.teachers[1], room=self.rooms[0])
            TimetableEntry.objects.create(section=self.sections["grade8"], day=day, time_slot=self.timeslots[4],
                                          subject=self.subjects["math"], teacher=self.teachers[5], room=self.rooms[4])
            TimetableEntry.objects.create(section=self.sections["grade8"], day=day, time_slot=self.timeslots[5],
                                          subject=self.subjects["english"], teacher=self.teachers[5], room=self.rooms[4])

    # ------------------------------------------------------- attendance & leave
    def attendance_and_leaves(self):
        from academics.models import Holiday
        from attendance.models import StaffAttendance, StudentAttendance
        from leaves.models import LeaveRequest, LeaveType
        from people.models import Employee
        Holiday.objects.create(title="Eid-ul-Adha vacation", kind="islamic", start_date=self.today + timedelta(days=60),
                               end_date=self.today + timedelta(days=67))
        Holiday.objects.create(title="Pakistan Day", kind="national", start_date=date(self.year.end_date.year, 3, 23),
                               end_date=date(self.year.end_date.year, 3, 23))
        for i in range(14, 0, -1):
            d = self.today - timedelta(days=i)
            if d.weekday() == 6:
                continue
            for st in self.students:
                status = random.choices(["present", "absent", "late"], [88, 7, 5])[0]
                StudentAttendance.objects.create(student=st, section=st.section, date=d, status=status,
                                                 marked_by=st.section.class_teacher)
            for emp in Employee.objects.all():
                status = random.choices(["present", "late", "absent"], [90, 7, 3])[0]
                StaffAttendance.objects.create(employee=emp, date=d, status=status,
                                               check_in=None if status == "absent" else time(7, random.randint(10, 45)),
                                               check_out=None if status == "absent" else time(13, random.randint(30, 59)))
        LT = LeaveType.objects.create
        casual = LT(name="Casual leave", code="CL", applies_to="staff", days_per_year=10)
        sick = LT(name="Sick leave", code="SL", applies_to="both", days_per_year=12)
        LT(name="Hajj / Umrah leave", code="HJ", applies_to="staff", days_per_year=40, requires_document=True)
        LT(name="Unpaid leave", code="UL", applies_to="staff", days_per_year=0, is_paid=False)
        home = LT(name="Home visit (students)", code="HV", applies_to="student", days_per_year=15)
        LeaveRequest.objects.create(user=self.teachers[3], applied_by=self.teachers[3], leave_type=casual,
                                    start_date=self.today + timedelta(days=3), end_date=self.today + timedelta(days=4),
                                    reason="Family wedding in Hyderabad", substitute=self.teachers[1])
        LeaveRequest.objects.create(user=self.students[0].user, applied_by=self.parents[0], leave_type=home,
                                    start_date=self.today + timedelta(days=1), end_date=self.today + timedelta(days=2),
                                    reason="Visiting grandparents")
        LeaveRequest.objects.create(user=self.teachers[5], applied_by=self.teachers[5], leave_type=sick,
                                    start_date=self.today - timedelta(days=6), end_date=self.today - timedelta(days=6),
                                    reason="Fever", status="approved", review_remarks="Get well soon")

    # -------------------------------------------------------------------- exams
    def exams(self):
        from exams.models import Certificate, Exam, ExamPaper, GradeScale, Mark
        for name, lo, hi, gp, ok, rem in [("Mumtaz (Excellent)", 80, 100, 4, True, "ممتاز"),
                                          ("Jayyid Jiddan (Very good)", 70, 79.99, 3.5, True, "جيد جداً"),
                                          ("Jayyid (Good)", 60, 69.99, 3, True, "جيد"),
                                          ("Maqbool (Pass)", 40, 59.99, 2, True, "مقبول"),
                                          ("Rasib (Fail)", 0, 39.99, 0, False, "راسب")]:
            GradeScale.objects.create(name=name, min_percentage=lo, max_percentage=hi, grade_point=gp, is_pass=ok, remarks=rem)
        exam = Exam.objects.create(name="First Quarterly Exam", kind="quarterly", academic_year=self.year,
                                   start_date=self.today - timedelta(days=30), end_date=self.today - timedelta(days=25),
                                   is_published=True)
        Exam.objects.create(name="Half-yearly Exam", kind="half_yearly", academic_year=self.year,
                            start_date=self.today + timedelta(days=40), end_date=self.today + timedelta(days=47))
        oola = self.sections["oola"]
        for i, key in enumerate(["nahw", "sarf", "fiqh", "hadith", "arabic"]):
            paper = ExamPaper.objects.create(exam=exam, section=oola, subject=self.subjects[key],
                                             date=exam.start_date + timedelta(days=i), start_time=time(8, 0),
                                             end_time=time(11, 0), room=self.rooms[2], max_marks=100, pass_marks=40,
                                             examiner=self.subjects[key].assignments.first().teacher)
            for st in oola.students.all():
                Mark.objects.create(paper=paper, student=st, marks_obtained=Decimal(random.randint(45, 98)),
                                    entered_by=paper.examiner)
        Certificate.objects.create(person=self.students[12].user, kind="character", title="Character certificate",
                                   details="has been a student of good character and conduct.", issued_by=self.staff[R.PRINCIPAL])

    # --------------------------------------------------------------------- hifz
    def hifz(self):
        from hifz.models import HifzRecord, JuzProgress
        hifz_students = [s for s in self.students if s.section == self.sections["hifz"]]
        for n, st in enumerate(hifz_students):
            done = 3 + n * 2
            for j in range(1, done + 1):
                JuzProgress.objects.create(student=st, juz=31 - j, status="tested" if j < done else "memorized",
                                           completed_on=self.today - timedelta(days=(done - j) * 30), test_score=85 + j % 10,
                                           tested_by=self.teachers[1] if j < done else None)
            JuzProgress.objects.create(student=st, juz=31 - done - 1, status="in_progress", started_on=self.today - timedelta(days=12))
            for i in range(10, 0, -1):
                d = self.today - timedelta(days=i)
                if d.weekday() == 6:
                    continue
                HifzRecord.objects.create(student=st, date=d, teacher=self.teachers[1], sabaq_surah=random.choice([2, 3, 4, 18, 36]),
                                          sabaq_from_ayah=10 + i, sabaq_to_ayah=17 + i, sabaq_quality=random.choice(["excellent", "good", "average"]),
                                          sabqi_juz=31 - done, sabqi_quantity="1/4 para", sabqi_quality=random.choice(["excellent", "good"]),
                                          manzil_juz=f"{31 - done + 1}-{30}", manzil_quality=random.choice(["good", "average"]),
                                          mistakes=random.randint(0, 4), hesitations=random.randint(0, 3), tajweed_rating=random.randint(6, 10))

    def program_images(self):
        """Attach the bundled illustrations (website/demo_assets/programs/<slug>.jpg) and Arabic titles."""
        from pathlib import Path

        from django.core.files import File

        from website.models import Program
        arabic = {"nazra": "القاعدة النورانية والناظرة", "alimah": "عالمة", "tajweed": "التجويد والقراءات",
                  "ifta": "التخصص في الإفتاء", "online": "التعليم عن بعد"}
        folder = Path(__file__).resolve().parents[3] / "website" / "demo_assets" / "programs"
        for program in Program.objects.all():
            if not program.title_arabic and program.slug in arabic:
                program.title_arabic = arabic[program.slug]
            img = folder / f"{program.slug}.jpg"
            if img.exists() and not program.image:
                with img.open("rb") as fh:
                    program.image.save(f"{program.slug}.jpg", File(fh), save=False)
            program.save()

    # -------------------------------------------------------------- biometrics
    def biometrics(self):
        from attendance.biometric import auto_enroll, record_punches
        from attendance.models import BiometricDevice, BiometricEnrollment
        gate = BiometricDevice.objects.create(name="Main gate (staff)", serial_number="DEMO-ZK-0001", audience="staff",
                                              location="Main entrance", notes="Demo device — replace with your real SN")
        BiometricDevice.objects.create(name="Hostel / boys block", serial_number="DEMO-ZK-0002", audience="students", location="Hostel")
        auto_enroll("all", "id")
        tz = timezone.get_current_timezone()
        base = datetime.combine(self.today, time(7, 0), tzinfo=tz)
        rows = []
        for i, t in enumerate(self.teachers):
            pin = BiometricEnrollment.objects.get(user=t).pin
            rows.append({"pin": pin, "time": base + timedelta(minutes=5 + i * 9), "direction": "in", "verify": "fingerprint"})
        rows.append({"pin": "99999", "time": base + timedelta(minutes=20), "direction": "in", "verify": "fingerprint"})  # unknown PIN
        record_punches(gate, rows, "push")

    # ---------------------------------------------------------- quran programs
    def quran_programs(self):
        from hifz.models import ChecklistItem, HifzRecord, JuzProgress, QaidaLesson, QaidaProgress, StudentChecklist
        from hifz.services import record_completion, set_tarjuma
        lessons = list(QaidaLesson.objects.all())
        nazra = [s for s in self.students if s.section == self.sections["nazra"]]
        for n, st in enumerate(nazra):
            if n < 2:  # still on Qaida
                for lesson in lessons[: 6 + n * 4]:
                    QaidaProgress.objects.create(student=st, lesson=lesson, status="passed", checked_by=self.teachers[3],
                                                 passed_on=self.today - timedelta(days=(20 - lesson.number) * 5))
                QaidaProgress.objects.create(student=st, lesson=lessons[6 + n * 4], status="in_progress")
            else:  # Qaida finished, reading Nazra
                for lesson in lessons:
                    QaidaProgress.objects.create(student=st, lesson=lesson, status="passed", checked_by=self.teachers[3],
                                                 passed_on=self.today - timedelta(days=200 - lesson.number * 5))
                record_completion(st, "qaida", self.teachers[3])
                for j in range(1, 6 + n * 3):
                    JuzProgress.objects.create(student=st, program="nazra", juz=j, status="memorized",
                                               completed_on=self.today - timedelta(days=(12 - j) * 7))
                JuzProgress.objects.create(student=st, program="nazra", juz=6 + n * 3, status="in_progress")
                if n == 3:
                    record_completion(st, "nazra", self.teachers[3], remarks="First khatm, Alhamdulillah")
            for i in range(6, 0, -1):
                d = self.today - timedelta(days=i)
                if d.weekday() != 6:
                    HifzRecord.objects.create(student=st, date=d, program="qaida" if n < 2 else "nazra", teacher=self.teachers[3],
                                              sabaq_lines=random.randint(5, 15), sabaq_quality=random.choice(["excellent", "good", "average"]),
                                              mistakes=random.randint(0, 5), tajweed_rating=random.randint(5, 9))
        alima = [s for s in self.students if s.section == self.sections["alima"]]
        for n, st in enumerate(alima):
            for surah in [1, *range(114, 114 - 10 - n * 4, -1)]:
                set_tarjuma(st, surah, "tested" if surah != 114 - 9 - n * 4 else "completed", self.teachers[4], test_score=80 + n)
            set_tarjuma(st, 2, "in_progress", self.teachers[4], ayahs_done=20 + n * 15)
        items = list(ChecklistItem.objects.all())
        for st in self.students:
            for item in items:
                if item.category in ("kalima", "dua", "surah", "namaz") and random.random() < 0.6:
                    StudentChecklist.objects.create(student=st, item=item, status=random.choice(["learned", "tested", "learning"]),
                                                    score=random.randint(6, 10), checked_by=st.section.class_teacher)
            if st.section == self.sections["hifz"]:
                for item in items:
                    if item.category == "tajweed" and item.order <= 12:
                        StudentChecklist.objects.create(student=st, item=item, status="tested", score=8, checked_by=self.teachers[1])

    # ---------------------------------------------------------------------- lms
    def lms(self):
        from liveclasses.models import LiveClass
        from liveclasses.providers import provision
        from lms.models import Assignment, Choice, Course, Homework, Lesson, Module, Question, Quiz
        oola = self.sections["oola"]
        course = Course.objects.create(title="Hidayat-un-Nahw — Arabic Syntax", code="NHW-101", subject=self.subjects["nahw"],
                                       section=oola, teacher=self.teachers[2], issue_certificate=True,
                                       description="A complete course on classical Arabic syntax based on Hidayat-un-Nahw.")
        m1 = Module.objects.create(course=course, title="Introduction: Kalimah and its types", order=1)
        m2 = Module.objects.create(course=course, title="Al-Marfu'at (Nominative cases)", order=2)
        Lesson.objects.create(module=m1, title="What is Ilm-un-Nahw?", order=1, kind="text",
                              content="<p>Nahw is the science by which the endings of Arabic words are known "
                                      "in terms of <b>i'rab</b> and <b>bina'</b>.</p>")
        Lesson.objects.create(module=m1, title="Ism, Fi'l and Harf (video)", order=2, kind="video",
                              media_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ", duration_minutes=18)
        Lesson.objects.create(module=m2, title="Al-Fa'il (The doer)", order=1, kind="text",
                              content="<p>The fa'il is always marfu'. Example: <span dir='rtl'>جاءَ زيدٌ</span></p>")
        Assignment.objects.create(course=course, title="Identify the Fa'il in 10 sentences", instructions="Write the i'rab of each.",
                                  due_at=timezone.now() + timedelta(days=5), max_marks=10, created_by=self.teachers[2])
        quiz = Quiz.objects.create(course=course, title="Quiz 1: Basics of Kalimah", time_limit_minutes=10, max_attempts=2)
        q1 = Question.objects.create(quiz=quiz, text="How many types of Kalimah are there?", order=1)
        for txt, ok in [("Two", False), ("Three", True), ("Four", False)]:
            Choice.objects.create(question=q1, text=txt, is_correct=ok)
        q2 = Question.objects.create(quiz=quiz, text="'Fi'l' indicates a meaning tied to time.", kind="true_false", order=2)
        Choice.objects.create(question=q2, text="True", is_correct=True)
        Choice.objects.create(question=q2, text="False", is_correct=False)
        Question.objects.create(quiz=quiz, text="Define Harf in your own words.", kind="short", marks=2, order=3)
        Course.objects.create(title="Seerah of the Prophet ﷺ (open course)", code="SRH-OPEN", teacher=self.teachers[4],
                              enrollment_type="open", description="An open course for all students.")
        Homework.objects.create(section=oola, subject=self.subjects["sarf"], title="Gardan of نَصَرَ",
                                description="Memorise and write the full gardan of nasara.", due_date=self.today + timedelta(days=1),
                                created_by=self.teachers[2])
        start = timezone.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
        for i, (title, sec, subj, teacher) in enumerate([("Nahw revision session", oola, "nahw", 2),
                                                         ("Online Tajweed class", self.sections["hifz"], "hifz", 1)]):
            lc = LiveClass(title=title, section=sec, subject=self.subjects[subj], teacher=self.teachers[teacher],
                           course=course if i == 0 else None, scheduled_start=start + timedelta(days=i), duration_minutes=45)
            lc.provider_error = provision(lc)
            lc.save()

    # ------------------------------------------------------------------ finance
    def finance(self):
        from finance.models import (Concession, Donation, Donor, Expense, ExpenseCategory, FeeHead, FeeStructure,
                                    OtherIncome, Payment, SalaryComponent)
        from finance.services import generate_invoices, generate_payroll
        from people.models import Employee
        tuition = FeeHead.objects.create(name="Tuition fee", kind="tuition")
        hostel = FeeHead.objects.create(name="Hostel & mess", kind="hostel")
        exam = FeeHead.objects.create(name="Examination fee", kind="exam")
        FeeHead.objects.create(name="Admission fee", kind="admission")
        for key, amt in [("hifz", 1500), ("nazra", 1000), ("dars", 2000), ("alima", 2000), ("modern", 3000)]:
            FeeStructure.objects.create(name=f"{self.dept[key].name} tuition", academic_year=self.year, department=self.dept[key],
                                        fee_head=tuition, amount=amt)
        FeeStructure.objects.create(name="Hostel & mess (boarders)", academic_year=self.year, fee_head=hostel, amount=4000,
                                    boarders_only=True)
        FeeStructure.objects.create(name="Annual exam fee", academic_year=self.year, fee_head=exam, amount=500, frequency="annual")
        for st in self.students:
            if st.is_orphan:
                Concession.objects.create(student=st, kind="percent", value=100, reason="orphan", funded_from="zakat")
            elif st.is_zakat_eligible:
                Concession.objects.create(student=st, kind="percent", value=50, reason="needy", funded_from="zakat")
        acct = self.staff[R.ACCOUNTANT]
        for months_ago in (2, 1, 0):
            period = (self.today.replace(day=1) - timedelta(days=months_ago * 28)).replace(day=1)
            generate_invoices(period=period, due_date=period + timedelta(days=9), frequencies=["monthly"], created_by=acct)
        from finance.models import Invoice
        for inv in Invoice.objects.filter(status="unpaid"):
            if inv.period and inv.period < self.today.replace(day=1) and random.random() < 0.8:
                Payment.objects.create(invoice=inv, amount=inv.total, method=random.choice(["cash", "bank", "jazzcash"]),
                                       date=inv.due_date - timedelta(days=2), received_by=acct, submitted_by=acct)
        donors = [Donor.objects.create(name=n, phone=f"0301{i:07d}", city="Karachi", is_recurring=i % 2 == 0)
                  for i, n in enumerate(["Haji Abdul Sattar", "Sheikh Brothers Traders", "Anonymous well-wisher", "Al-Noor Foundation"])]
        for i in range(12):
            d = donors[i % 4]
            Donation.objects.create(donor=d, donor_name=d.name, phone=d.phone, fund=random.choice(["zakat", "sadaqah", "lillah", "general", "construction"]),
                                    amount=Decimal(random.choice([5000, 10000, 25000, 50000, 100000])),
                                    date=self.today - timedelta(days=random.randint(0, 80)), method=random.choice(["cash", "bank"]),
                                    received_by=acct, sponsored_student=self.students[3] if i == 0 else None)
        Donation.objects.create(donor_name="Online donor", phone="03111111111", fund="sadaqah", amount=3000, status="pledged",
                                method="easypaisa", reference="EP123456")
        cats = {n: ExpenseCategory.objects.create(name=n) for n in ["Utilities", "Kitchen & mess", "Maintenance", "Books & stationery", "Student welfare (Zakat)"]}
        for i in range(15):
            cat = random.choice(list(cats))
            Expense.objects.create(category=cats[cat], title=f"{cat} — invoice {100 + i}", amount=Decimal(random.randint(3, 60) * 1000),
                                   fund="zakat" if "Zakat" in cat else "general", date=self.today - timedelta(days=random.randint(0, 80)),
                                   paid_to=random.choice(["K-Electric", "Al-Madina Store", "Bismillah Builders"]), created_by=acct,
                                   approved_by=self.staff[R.PRINCIPAL])
        Expense.objects.create(category=cats["Maintenance"], title="Masjid fans replacement", amount=45000, status="pending", created_by=acct)
        OtherIncome.objects.create(title="Shop rent (waqf property)", fund="waqf", amount=30000, date=self.today - timedelta(days=10))
        for emp in Employee.objects.all()[:10]:
            SalaryComponent.objects.create(employee=emp, kind="allowance", title="House rent", amount=emp.basic_salary * Decimal("0.2"))
            SalaryComponent.objects.create(employee=emp, kind="deduction", title="EOBI", amount=370)
        generate_payroll((self.today.replace(day=1) - timedelta(days=1)).replace(day=1))

    # ----------------------------------------------- library/hostel/transport/inventory
    def library_hostel_transport_inventory(self):
        from hostel.models import GatePass, Hostel, HostelAllocation, HostelRoom, MessMenu
        from inventory.models import Asset, AssetCategory, StockItem, StockMovement, Vendor
        from library.models import Book, BookCategory, BookIssue
        from transport.models import Route, RouteStop, TransportAssignment, Vehicle
        cats = {n: BookCategory.objects.create(name=n) for n in ["Tafseer", "Hadith", "Fiqh", "Seerah", "Arabic Grammar", "Urdu Literature"]}
        books = [("Tafseer Ibn Kathir", "Ibn Kathir", "Tafseer", "arabic", 8), ("Sahih al-Bukhari", "Imam al-Bukhari", "Hadith", "arabic", 10),
                 ("Ma'ariful Quran", "Mufti Muhammad Shafi", "Tafseer", "urdu", 5), ("Al-Hidayah", "Al-Marghinani", "Fiqh", "arabic", 6),
                 ("Ar-Raheeq al-Makhtum", "Safiur Rahman Mubarakpuri", "Seerah", "english", 4),
                 ("Hidayat-un-Nahw", "Shaykh Sirajuddin", "Arabic Grammar", "arabic", 30), ("Riyad-us-Saliheen", "Imam an-Nawawi", "Hadith", "arabic", 25),
                 ("Bahishti Zewar", "Maulana Ashraf Ali Thanvi", "Fiqh", "urdu", 12)]
        objs = [Book.objects.create(title=t, author=a, category=cats[c], language=l, total_copies=n, available_copies=n, shelf=f"R{i + 1}")
                for i, (t, a, c, l, n) in enumerate(books)]
        for i, st in enumerate(self.students[:5]):
            BookIssue.objects.create(book=objs[i], borrower=st.user, issued_on=self.today - timedelta(days=20 - i * 2),
                                     due_date=self.today - timedelta(days=6 - i * 2), issued_by=self.staff[R.LIBRARIAN])
            objs[i].available_copies -= 1
            objs[i].save()
        h = Hostel.objects.create(name="Dar-ul-Iqamah (Boys)", warden=self.staff[R.HOSTEL_WARDEN], capacity=60)
        rooms = [HostelRoom.objects.create(hostel=h, number=f"{100 + i}", floor="Ground", capacity=4) for i in range(1, 6)]
        for i, st in enumerate(s for s in self.students if s.is_boarder and s.user.gender == "male"):
            HostelAllocation.objects.create(student=st, room=rooms[i // 4], bed_no=str(i % 4 + 1))
        for day in range(7):
            MessMenu.objects.create(hostel=h, day=day, meal="breakfast", items="Paratha, chai, omelette")
            MessMenu.objects.create(hostel=h, day=day, meal="lunch", items=random.choice(["Daal chawal", "Chicken qorma, roti", "Aloo gosht"]))
            MessMenu.objects.create(hostel=h, day=day, meal="dinner", items=random.choice(["Sabzi, roti", "Biryani", "Chana, roti"]))
        boarder = next(s for s in self.students if s.is_boarder and s.guardian and s.guardian.user)
        GatePass.objects.create(student=boarder, reason="Weekend at home", out_time=timezone.now() + timedelta(days=2),
                                expected_return=timezone.now() + timedelta(days=3), escort_name=boarder.guardian.name,
                                applied_by=boarder.guardian.user)
        v = Vehicle.objects.create(registration_no="KHI-1234", kind="Coaster", capacity=25, driver_name="Akram", driver_phone="03001112233",
                                   insurance_expiry=self.today + timedelta(days=20))
        route = Route.objects.create(name="Route 1 — Gulshan / Johar", vehicle=v, monthly_fare=2500)
        stops = [RouteStop.objects.create(route=route, name=n, pickup_time=time(6, 45 + i * 5), order=i + 1)
                 for i, n in enumerate(["Johar Chowrangi", "Gulshan Chowrangi", "NIPA"])]
        for st in self.students[16:20]:
            TransportAssignment.objects.create(user=st.user, route=route, stop=random.choice(stops))
        vend = Vendor.objects.create(name="Al-Madina General Store", phone="0213333333")
        furn = AssetCategory.objects.create(name="Furniture")
        elec = AssetCategory.objects.create(name="Electronics")
        for i in range(1, 6):
            Asset.objects.create(name="Rehal / desk set", tag=f"FUR-{i:03d}", category=furn, room=self.rooms[i % 4], cost=3500, is_waqf=i % 2 == 0)
        Asset.objects.create(name="Projector", tag="ELC-001", category=elec, room=self.rooms[2], cost=85000, vendor=vend)
        for name, unit, qty, lvl in [("Rice", "kg", 250, 100), ("Flour (atta)", "kg", 80, 100), ("Chalk boxes", "box", 12, 10),
                                     ("Mushaf (Quran copies)", "pcs", 40, 20)]:
            item = StockItem.objects.create(name=name, unit=unit, reorder_level=lvl)
            StockMovement.objects.create(item=item, kind="in", quantity=qty, vendor=vend, recorded_by=self.staff[R.STORE_KEEPER])

    # ------------------------------------------------------------ communication
    def communication(self):
        from communication.models import Announcement, Complaint, Event, Message, ParentMeeting
        principal = self.staff[R.PRINCIPAL]
        Announcement.objects.create(title="Half-yearly exams date sheet released",
                                    body="The half-yearly examinations will begin next month. Check the portal for the date sheet.",
                                    priority="important", is_pinned=True, created_by=principal, notify=False)
        Announcement.objects.create(title="Staff meeting on Thursday after Zuhr", body="All asatiza are requested to attend.",
                                    audience=[R.TEACHER, R.ACADEMIC_COORDINATOR], created_by=principal, notify=False)
        Announcement.objects.create(title="Parents: fee submission reminder", body="Please clear dues by the 10th of each month.",
                                    audience=[R.PARENT], created_by=self.staff[R.ACCOUNTANT], notify=False)
        E = Event.objects.create
        E(title="Annual Jalsa & Dastar-bandi", slug="annual-jalsa", kind="jalsa", is_public=True, location="Jamia Masjid",
          start=timezone.now() + timedelta(days=20), description="Graduation ceremony for Huffaz and Ulama. All are invited.")
        E(title="Inter-madrasa Qira'at competition", slug="qiraat-competition", kind="competition", is_public=True,
          start=timezone.now() + timedelta(days=9), location="Main Hall")
        E(title="Parent-teacher meeting", slug="ptm-term-1", kind="ptm", start=timezone.now() + timedelta(days=5), audience=[R.PARENT, R.TEACHER])
        E(title="Seerah conference", slug="seerah-conference", kind="islamic", is_public=True, start=timezone.now() - timedelta(days=15))
        Message.objects.create(sender=self.parents[0], recipient=self.teachers[1], subject="Progress of my son",
                               body="Assalamu alaikum Qari sahib, how is Abdur Rahman's sabaq progressing?")
        Complaint.objects.create(submitted_by=self.parents[1], category="hostel", subject="Water cooler not working",
                                 description="The water cooler on the first floor has been out of order for 3 days.")
        ParentMeeting.objects.create(student=self.students[0], teacher=self.teachers[1], agenda="Hifz progress review",
                                     scheduled_at=timezone.now() + timedelta(days=5), status="scheduled", created_by=self.teachers[1])

    # ------------------------------------------------------------------ website
    def website(self):
        from website.models import FAQ, BoardMember, FatwaQuestion, GalleryAlbum, NewsPost, Page, Program, Slide, Stat, Testimonial
        P = Page.objects.create
        P(slug="about", title="About the University", subtitle="A beacon of Islamic learning", order=1, show_in_menu=True,
          body="<p>University of Muhammadia Saifia is a non-profit, residential Islamic seminary dedicated to the preservation of the "
               "Qur'an and the Sunnah. Our students study the classical Dars-e-Nizami curriculum under qualified Ulama with "
               "unbroken chains of transmission (asanid), alongside modern subjects so that they can serve society in every field.</p>"
               "<p>Today the University educates more than 1,200 students across its Baneen and Banaat campuses, with over 400 boarders "
               "whose food, accommodation and education are provided free of charge through the generosity of donors.</p>")
        P(slug="history", title="Our History", subtitle="From a single halqa in 1978 to a full university", order=2, show_in_menu=True,
          body="<h3>1978 — The beginning</h3><p>The University began as a single Hifz halqa in the courtyard of the local masjid, "
               "founded by Hazrat Maulana Abdul Ghafoor (rahimahullah) with seven students.</p>"
               "<h3>1986 — Dars-e-Nizami</h3><p>The first classes of the eight-year Alim course were started and the University was "
               "affiliated with Wifaq-ul-Madaris Al-Arabia Pakistan.</p>"
               "<h3>1999 — Banaat campus</h3><p>A separate campus for girls was established, offering Hifz, Nazra and the Alimah course.</p>"
               "<h3>2010 — Dar-ul-Ifta</h3><p>The Takhassus fil Ifta department and Dar-ul-Ifta were founded to answer the "
               "religious questions of the public.</p>"
               "<h3>2020 — Online learning</h3><p>Live online classes were launched, allowing students across the world to study with our asatiza.</p>")
        P(slug="vision-mission", title="Vision & Mission", order=3, show_in_menu=True,
          body="<h3>Vision</h3><p>To produce Huffaz and Ulama who embody knowledge, taqwa and good character and who serve the Ummah "
               "with wisdom.</p><h3>Mission</h3><ul><li>Preserve the Qur'an through Hifz with correct Tajweed.</li>"
               "<li>Teach the Islamic sciences with authentic chains of transmission.</li><li>Provide free education, food and "
               "boarding to deserving students.</li><li>Combine religious and modern education.</li></ul>")
        P(slug="founder-message", title="Message from the Founder", order=4,
          body="<p>“Knowledge is a trust from Allah. Our duty is to pass it on as we received it — with sincerity and adab.”</p>")
        P(slug="rules", title="Rules & Code of Conduct", order=5,
          body="<ul><li>Students must attend all five daily prayers in congregation.</li><li>Uniform: white kurta and topi.</li>"
               "<li>Mobile phones are not allowed in the hostel.</li><li>Minimum 75% attendance is required to sit exams.</li></ul>")
        P(slug="admission-policy", title="Admission Policy", order=6,
          body="<p>Admissions open every Shawwal. An entry test of Qur'an recitation and basic knowledge is held for all applicants. "
               "Orphans and needy students receive full scholarships.</p>")
        Program.objects.create(slug="hifz", title="Hifz-ul-Quran", title_arabic="حفظ القرآن", department=self.dept["hifz"], icon="quran", order=1,
                               summary="Memorise the complete Qur'an with Tajweed under expert Qurra.", duration="2.5 – 3 years",
                               eligibility="Age 7–14, Nazra complete", timings="After Fajr – Zuhr",
                               description="<p>Daily sabaq, sabqi and manzil with individual attention and monthly para tests.</p>")
        Program.objects.create(slug="nazra", title="Noorani Qaida & Nazra", department=self.dept["nazra"], icon="book", order=2,
                               summary="Learn to read the Qur'an correctly from the very first letter.", duration="1 – 1.5 years",
                               eligibility="Age 5+")
        Program.objects.create(slug="alim", title="Dars-e-Nizami (Alim Course)", title_arabic="درس نظامي", department=self.dept["dars"],
                               icon="graduation", order=3, summary="Eight-year classical curriculum: Arabic, Fiqh, Hadith, Tafseer and more.",
                               duration="8 years", eligibility="Middle pass or equivalent")
        Program.objects.create(slug="alimah", title="Alimah Course (Girls)", department=self.dept["alima"], icon="graduation", order=4,
                               summary="A complete Alimah programme in a secure purdah environment.", duration="6 years")
        Program.objects.create(slug="tajweed", title="Tajweed & Qira'at", department=self.dept["tajweed"], icon="mic", order=5,
                               summary="Perfect your recitation with the rules of Tajweed; Qira'at Sab'ah for advanced students.",
                               duration="1 year")
        Program.objects.create(slug="tarjuma", title="Tarjuma-tul-Quran", title_arabic="ترجمة القرآن", department=self.dept["tarjuma"],
                               icon="book", order=5, summary="Understand the Qur'an word by word: translation, basic grammar and key tafseer.",
                               duration="2 years (part-time available)", eligibility="Nazra complete; age 12+", timings="Evening & weekend batches",
                               description="<p>Surah-by-surah word-by-word translation with essential Arabic grammar, lessons from each "
                                           "surah and regular tests. Progress is tracked ayah by ayah, and a certificate is issued on completion.</p>")
        Program.objects.create(slug="ifta", title="Takhassus fil Ifta", department=self.dept["ifta"], icon="scale", order=6,
                               summary="Two-year specialisation in Islamic jurisprudence and issuing fatawa.", duration="2 years",
                               eligibility="Alim / Fazil")
        Program.objects.create(slug="online", title="Online Quran Classes", icon="video", order=7,
                               summary="Live one-to-one and group classes for students anywhere in the world.", duration="Flexible")
        for i, (t, sm, cat) in enumerate([("42 Huffaz complete the Qur'an this year", "Alhamdulillah, the annual Hifz completion ceremony was held.", "Achievements"),
                                          ("New computer lab inaugurated", "Students of the modern education wing now have a 25-seat lab.", "Campus"),
                                          ("Results of Wifaq-ul-Madaris exams", "Our students secured top positions in the board exams.", "Results")]):
            NewsPost.objects.create(slug=f"news-{i + 1}", title=t, summary=sm, category=cat, body=f"<p>{sm}</p><p>More details coming soon.</p>",
                                    published_at=timezone.now() - timedelta(days=i * 9), author=self.staff[R.MEDIA_MANAGER])
        self.program_images()
        GalleryAlbum.objects.create(title="Annual Jalsa 2025", description="Dastar-bandi ceremony")
        Testimonial.objects.create(name="Br. Abdul Basit", role="Parent", quote="My son completed his Hifz here in 2.5 years. The asatiza care for every child.")
        Testimonial.objects.create(name="Mufti Hammad", role="Alumnus, 2012", quote="The University gave me knowledge, adab and a sanad I am proud of.")
        Testimonial.objects.create(name="Sr. Umm Salma", role="Parent", quote="The Banaat campus is safe and the teachers are excellent.")
        for q, a, c in [("When do admissions open?", "Every year in Shawwal. Online applications are accepted year-round.", "Admissions"),
                        ("Is there a fee?", "Fees are minimal; orphans and needy students study free with full boarding.", "Fees"),
                        ("Do you offer hostel facilities?", "Yes, for boys and girls on separate campuses with meals.", "Hostel"),
                        ("Can I donate my Zakat?", "Yes. Zakat is kept in a separate fund and spent only on eligible students.", "Donations"),
                        ("Do you offer online classes?", "Yes — live Qur'an and Tajweed classes are available worldwide.", "Online")]:
            FAQ.objects.create(question=q, answer=a, category=c)
        BoardMember.objects.create(name="Hazrat Maulana Abdul Ghafoor (rahimahullah)", title="Founder (1978)", is_founder=True, order=1,
                                   bio="Founded the University with seven students and served it for 35 years.")
        BoardMember.objects.create(name="Mufti Muhammad Rafiq", title="Mohtamim (Principal)", order=2)
        BoardMember.objects.create(name="Haji Abdul Sattar", title="Member, Majlis-e-Shura", order=3)
        for i, (lbl, val) in enumerate([("Students", "1,200+"), ("Huffaz graduated", "2,500+"), ("Ulama graduated", "650+"),
                                        ("Years of service", "47")]):
            Stat.objects.create(label=lbl, value=val, order=i)
        Slide.objects.create(title="Preserving the words of Allah", subtitle="Hifz, Nazra & Tajweed under qualified Qurra",
                             cta_text="Apply for admission", cta_link="/admissions", order=1)
        Slide.objects.create(title="Your Zakat educates an orphan", subtitle="Sponsor a student's education and boarding",
                             cta_text="Donate now", cta_link="/donate", order=2)
        mufti = self.staff[R.MUFTI]
        FatwaQuestion.objects.create(name="Ahmed", title="Zakat on gold jewellery", category="Zakat", fatwa_no="F-2026-0001",
                                     question="Is zakat due on gold jewellery that my wife wears daily?",
                                     answer="According to the Hanafi madhhab, zakat is obligatory on gold jewellery whether worn or "
                                            "not, once it reaches the nisab and a lunar year passes. And Allah knows best.",
                                     status="answered", answered_at=timezone.now() - timedelta(days=3), assigned_to=mufti)
        FatwaQuestion.objects.create(name="Bilal", title="Combining prayers while travelling", category="Salah",
                                     question="Can I combine Zuhr and Asr while on a journey?")
