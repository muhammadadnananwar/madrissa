"""
End-to-end API tests against the demo data set.

Run:  python manage.py test
"""
from datetime import timedelta

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from accounts.models import User
from core.roles import R
from core.viewsets import REGISTRY


class DemoDataTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo", verbosity=0, stdout=open("/dev/null", "w"))

    def client_for(self, username):
        c = APIClient()
        c.force_authenticate(User.objects.get(username=username))
        return c


class SmokeTests(DemoDataTestCase):
    ROLES = ["admin", "principal", "coordinator", "accountant", "hr", "admissions", "exams", "librarian", "warden",
             "transport", "reception", "store", "mufti", "media", "staff", "qari.yusuf", "student1", "parent1"]

    def test_every_resource_list_and_meta_for_every_role(self):
        for username in self.ROLES:
            c = self.client_for(username)
            menu = c.get("/api/meta/")
            self.assertEqual(menu.status_code, 200, username)
            for key, vs in REGISTRY.items():
                user = User.objects.get(username=username)
                r = c.get(f"/api/{key}/")
                if vs.can_list(user):
                    self.assertEqual(r.status_code, 200, f"{username} list {key}: {r.content[:200]}")
                    self.assertEqual(c.get(f"/api/meta/{key}/").status_code, 200, f"{username} meta {key}")
                else:
                    self.assertIn(r.status_code, (403, 404), f"{username} should not list {key}")

    def test_dashboard_for_every_role(self):
        for username in self.ROLES:
            r = self.client_for(username).get("/api/dashboard/")
            self.assertEqual(r.status_code, 200, f"{username}: {r.content[:300]}")

    def test_csv_export(self):
        r = self.client_for("admin").get("/api/students/export/")
        self.assertEqual(r.status_code, 200)
        self.assertIn("Admission No", r.content.decode())

    def test_login_and_me(self):
        c = APIClient()
        r = c.post("/api/auth/login/", {"username": "student1", "password": "madrasa123"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        me = c.get("/api/auth/me/")
        self.assertEqual(me.data["role"], R.STUDENT)
        self.assertIn("student", me.data)

    def test_profile360(self):
        st = User.objects.get(username="student1")
        self.assertEqual(self.client_for("admin").get(f"/api/people/profile/{st.id}/").status_code, 200)
        self.assertEqual(self.client_for("parent1").get(f"/api/people/profile/{st.id}/").status_code, 200)
        other = User.objects.get(username="student5")
        self.assertEqual(self.client_for("student1").get(f"/api/people/profile/{other.id}/").status_code, 403)


class PermissionTests(DemoDataTestCase):
    def test_student_sees_only_self(self):
        r = self.client_for("student1").get("/api/students/")
        self.assertEqual(r.data["count"], 1)

    def test_parent_sees_only_children(self):
        r = self.client_for("parent1").get("/api/students/")
        self.assertEqual(r.data["count"], 2)  # parent1 has two children in the demo data

    def test_student_cannot_create_invoice(self):
        r = self.client_for("student1").post("/api/invoices/", {"title": "x"}, format="json")
        self.assertEqual(r.status_code, 403)

    def test_cannot_escalate_role_through_student_form(self):
        from people.models import Student
        st = Student.objects.first()
        r = self.client_for("admissions").patch(f"/api/students/{st.id}/", {"role": "super_admin"}, format="json")
        self.assertEqual(r.status_code, 400)
        st.user.refresh_from_db()
        self.assertEqual(st.user.role, R.STUDENT)

    def test_students_never_see_host_links(self):
        from liveclasses.models import LiveClass
        lc = LiveClass.objects.get(title="Nahw revision session")
        lc.host_url = "https://zoom.example/start/secret"
        lc.save()
        student = lc.section.students.first().user.username
        self.assertNotIn("host_url", self.client_for(student).get(f"/api/live-classes/{lc.id}/").data)
        self.assertIn("host_url", self.client_for("ustadh.imran").get(f"/api/live-classes/{lc.id}/").data)

    def test_teacher_only_marks_own_sections(self):
        from academics.models import Section
        other = Section.objects.exclude(class_teacher__username="qari.yusuf").exclude(
            assignments__teacher__username="qari.yusuf").first()
        r = self.client_for("qari.yusuf").get(f"/api/attendance/sheet/?section={other.id}")
        self.assertEqual(r.status_code, 403)


class WorkflowTests(DemoDataTestCase):
    def test_attendance_bulk_mark(self):
        from academics.models import Section
        sec = Section.objects.get(class_teacher__username="qari.yusuf")
        c = self.client_for("qari.yusuf")
        sheet = c.get(f"/api/attendance/sheet/?section={sec.id}").data
        records = [{"student": s["student"], "status": "present"} for s in sheet["students"]]
        r = c.post("/api/attendance/bulk/", {"section": sec.id, "date": str(timezone.localdate()), "records": records}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["count"], len(records))

    def test_staff_self_check_in_out(self):
        c = self.client_for("qari.yusuf")
        from attendance.models import StaffAttendance
        StaffAttendance.objects.filter(employee__user__username="qari.yusuf", date=timezone.localdate()).delete()
        self.assertEqual(c.post("/api/attendance/staff/self/", {"action": "check_in"}, format="json").status_code, 200)
        r = c.post("/api/attendance/staff/self/", {"action": "check_out"}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertIsNotNone(r.data["today"]["check_out"])

    def test_leave_apply_and_approve_marks_attendance(self):
        from leaves.models import LeaveType
        from attendance.models import StudentAttendance
        lt = LeaveType.objects.get(code="SL")
        student = User.objects.get(username="student1")
        start = timezone.localdate() + timedelta(days=10)
        while start.weekday() == 6:
            start += timedelta(days=1)
        r = self.client_for("parent1").post("/api/leave-requests/", {
            "user": student.id, "leave_type": lt.id, "start_date": str(start), "end_date": str(start), "reason": "Fever"},
            format="json")
        self.assertEqual(r.status_code, 201, r.content)
        r2 = self.client_for("qari.yusuf").post(f"/api/leave-requests/{r.data['id']}/approve/", {}, format="json")
        self.assertEqual(r2.status_code, 200, r2.content)
        self.assertTrue(StudentAttendance.objects.filter(student__user=student, date=start, status="leave").exists())

    def test_fee_collection_and_parent_proof(self):
        from finance.models import Invoice
        inv = Invoice.objects.filter(status="unpaid", total__gt=0, student__guardian__user__username="parent1").first() \
            or Invoice.objects.filter(status="unpaid", total__gt=0).first()
        r = self.client_for("accountant").post(f"/api/invoices/{inv.id}/collect/", {"amount": "100", "method": "cash"}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        inv.refresh_from_db()
        self.assertEqual(inv.status, "partial")
        self.assertEqual(self.client_for("accountant").get("/api/finance/summary/").status_code, 200)

    def test_generate_invoices_and_payroll(self):
        c = self.client_for("accountant")
        nxt = (timezone.localdate().replace(day=1) + timedelta(days=32)).strftime("%Y-%m")
        r = c.post("/api/finance/generate-invoices/", {"period": nxt}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertGreater(r.data["created"], 0)
        r = c.post("/api/finance/payroll/generate/", {"month": timezone.localdate().strftime("%Y-%m")}, format="json")
        self.assertEqual(r.status_code, 200, r.content)

    def test_quiz_attempt_autograde(self):
        from lms.models import Quiz
        quiz = Quiz.objects.get(title__startswith="Quiz 1")
        student = quiz.course.section.students.first().user.username
        c = self.client_for(student)
        start = c.post(f"/api/quizzes/{quiz.id}/start/", {}, format="json")
        self.assertEqual(start.status_code, 200, start.content)
        answers = []
        for q in quiz.questions.all():
            correct = list(q.choices.filter(is_correct=True).values_list("id", flat=True))
            answers.append({"question": q.id, "choices": correct, "text": "A particle"})
        r = c.post(f"/api/quiz-attempts/{start.data['attempt']}/submit/", {"answers": answers}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["status"], "submitted")  # short answer awaits manual grading
        self.assertEqual(float(r.data["score"]), 2.0)

    def test_course_outline_and_lesson_complete(self):
        from lms.models import Course
        course = Course.objects.get(code="NHW-101")
        student = course.section.students.first().user.username
        c = self.client_for(student)
        outline = c.get(f"/api/courses/{course.id}/outline/")
        self.assertEqual(outline.status_code, 200, outline.content)
        lesson = outline.data["modules"][0]["lessons"][0]["id"]
        r = c.post(f"/api/lessons/{lesson}/complete/", {}, format="json")
        self.assertEqual(r.status_code, 200)
        self.assertGreater(r.data["progress"], 0)

    def test_live_class_join_marks_attendance(self):
        from attendance.models import StudentAttendance
        from liveclasses.models import LiveClass
        lc = LiveClass.objects.get(title="Nahw revision session")
        lc.scheduled_start = timezone.now()
        lc.save()
        self.assertTrue(lc.join_url.startswith("https://"))
        student = lc.section.students.first()
        r = self.client_for(student.user.username).post(f"/api/live-classes/{lc.id}/join/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(StudentAttendance.objects.filter(student=student, source="live_class").exists())
        end = self.client_for("ustadh.imran").post(f"/api/live-classes/{lc.id}/end/", {}, format="json")
        self.assertEqual(end.status_code, 200, end.content)

    def test_exam_result_and_report_card(self):
        from exams.models import Exam
        from academics.models import Section
        exam = Exam.objects.get(name="First Quarterly Exam")
        sec = Section.objects.get(class_level__name="Darja Oola")
        r = self.client_for("exams").get(f"/api/exams/result/?exam={exam.id}&section={sec.id}")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(all(row["position"] or row["result"] == "Fail" for row in r.data["rows"]))
        st = sec.students.first()
        card = self.client_for(st.user.username).get(f"/api/exams/report-card/?student={st.id}")
        self.assertEqual(card.status_code, 200)
        self.assertEqual(len(card.data["cards"]), 1)

    def test_hifz_daily_sheet(self):
        from academics.models import Section
        sec = Section.objects.get(class_level__name="Hifz Class")
        c = self.client_for("qari.yusuf")
        sheet = c.get(f"/api/hifz/daily/?section={sec.id}")
        self.assertEqual(sheet.status_code, 200)
        sid = sheet.data["rows"][0]["student"]
        r = c.post("/api/hifz/daily/", {"section": sec.id, "date": str(timezone.localdate()), "program": "hifz",
                                         "records": [{"student": sid, "sabaq_surah": 2, "sabaq_from_ayah": 1, "sabaq_to_ayah": 5,
                                                      "sabaq_quality": "good", "mistakes": 1}]}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(c.get(f"/api/hifz/students/{sid}/").status_code, 200)

    def test_admission_to_enrollment(self):
        public = APIClient()
        r = public.post("/api/public/admission/", {
            "full_name": "Abdullah Test", "father_name": "Test Father", "gender": "male", "date_of_birth": "2014-01-01",
            "phone": "03001234567", "address": "Karachi", "guardian_name": "Test Father", "guardian_phone": "03007654321"},
            format="json")
        self.assertEqual(r.status_code, 201, r.content)
        from people.models import AdmissionApplication
        app = AdmissionApplication.objects.get(application_no=r.data["application_no"])
        status = public.get(f"/api/public/admission-status/?application_no={app.application_no}&phone=03007654321")
        self.assertEqual(status.status_code, 200)
        e = self.client_for("admissions").post(f"/api/admissions/{app.id}/enroll/", {}, format="json")
        self.assertEqual(e.status_code, 200, e.content)
        self.assertTrue(User.objects.filter(username=e.data["username"], role=R.STUDENT).exists())

    def test_library_issue_return(self):
        from library.models import Book
        book = Book.objects.filter(available_copies__gt=0, is_reference_only=False).first()
        c = self.client_for("librarian")
        borrower = User.objects.get(username="student20")
        r = c.post(f"/api/books/{book.id}/issue/", {"borrower": borrower.id}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        r = c.post(f"/api/book-issues/{r.data['issue_id']}/return_book/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.content)

    def test_messaging(self):
        teacher = User.objects.get(username="qari.yusuf")
        c = self.client_for("parent1")
        r = c.post("/api/messages/", {"recipient": teacher.id, "subject": "Hello", "body": "Salaam"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        inbox = self.client_for("qari.yusuf").get("/api/messages/?box=inbox")
        self.assertGreaterEqual(inbox.data["count"], 1)
        other_parent = User.objects.get(username="parent2")
        self.assertEqual(c.post("/api/messages/", {"recipient": other_parent.id, "subject": "x", "body": "y"},
                                format="json").status_code, 400)


class PublicApiTests(DemoDataTestCase):
    def test_public_endpoints(self):
        c = APIClient()
        for url in ["/api/public/site/", "/api/public/home/", "/api/public/pages/history/", "/api/public/programs/",
                    "/api/public/news/", "/api/public/events/", "/api/public/gallery/", "/api/public/teachers/",
                    "/api/public/board/", "/api/public/faqs/", "/api/public/downloads/", "/api/public/fatwas/",
                    "/api/public/library/", "/api/public/admission-options/"]:
            self.assertEqual(c.get(url).status_code, 200, url)

    def test_public_forms(self):
        c = APIClient()
        self.assertEqual(c.post("/api/public/contact/", {"name": "A", "subject": "Hi", "message": "Hello"}, format="json").status_code, 201)
        self.assertEqual(c.post("/api/public/donate/", {"donor_name": "A", "phone": "0300", "fund": "zakat", "amount": "1000"},
                                format="json").status_code, 201)
        self.assertEqual(c.post("/api/public/fatwa/ask/", {"name": "A", "title": "Q", "question": "?"}, format="json").status_code, 201)

    def test_certificate_verification(self):
        from exams.models import Certificate
        cert = Certificate.objects.first()
        r = APIClient().get(f"/api/public/verify-certificate/?code={cert.verification_code}")
        self.assertEqual(r.status_code, 200)
        self.assertTrue(r.data["valid"])


class QuranProgramTests(DemoDataTestCase):
    def setUp(self):
        from academics.models import Section
        self.section = Section.objects.get(class_level__name="Nazra Class")
        self.student = self.section.students.first()
        self.teacher = self.client_for(self.section.class_teacher.username)

    def test_qaida_completion_issues_certificate(self):
        from exams.models import Certificate
        from hifz.models import QaidaLesson, QaidaProgress, QuranCompletion
        QaidaProgress.objects.filter(student=self.student).delete()
        QuranCompletion.objects.filter(student=self.student).delete()
        for lesson in QaidaLesson.objects.all():
            r = self.teacher.post(f"/api/hifz/students/{self.student.id}/qaida/", {"lesson": lesson.id, "status": "passed"}, format="json")
            self.assertEqual(r.status_code, 200, r.content)
        self.assertTrue(r.data["completed"])
        self.assertTrue(QuranCompletion.objects.filter(student=self.student, kind="qaida").exists())
        self.assertTrue(Certificate.objects.filter(person=self.student.user, kind="qaida").exists())

    def test_nazra_khatm_records_completion_and_resets_grid(self):
        from exams.models import Certificate
        from hifz.models import QuranCompletion
        before = QuranCompletion.objects.filter(student=self.student, kind="nazra").count()
        for juz in range(1, 31):
            r = self.teacher.post(f"/api/hifz/students/{self.student.id}/juz/", {"program": "nazra", "juz": juz, "status": "memorized"}, format="json")
            self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["done"], 0)  # grid reset for the next khatm
        self.assertEqual(QuranCompletion.objects.filter(student=self.student, kind="nazra").count(), before + 1)
        self.assertTrue(Certificate.objects.filter(person=self.student.user, kind="nazra").exists())
        # Hifz grid is untouched by Nazra updates
        self.assertEqual(self.teacher.get(f"/api/hifz/students/{self.student.id}/programs/").data["hifz"]["done"], 0)

    def test_tarjuma_percentage_is_ayah_weighted(self):
        from hifz.models import TarjumaProgress
        TarjumaProgress.objects.filter(student=self.student).delete()
        self.teacher.post(f"/api/hifz/students/{self.student.id}/tarjuma/", {"surah": 1, "status": "completed"}, format="json")
        r = self.teacher.post(f"/api/hifz/students/{self.student.id}/tarjuma/", {"surah": 2, "status": "in_progress", "ayahs_done": 141}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["percentage"], round((7 + 141) / 6236 * 100, 1))

    def test_checklist_sheet_for_section(self):
        from hifz.models import ChecklistItem, StudentChecklist
        item = ChecklistItem.objects.get(title="Before eating")
        sheet = self.teacher.get(f"/api/hifz/checklist-sheet/?section={self.section.id}&item={item.id}")
        self.assertEqual(sheet.status_code, 200)
        records = [{"student": r["student"], "status": "tested", "score": 9} for r in sheet.data["rows"]]
        r = self.teacher.post("/api/hifz/checklist-sheet/", {"section": self.section.id, "item": item.id, "records": records}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(StudentChecklist.objects.filter(item=item, student__section=self.section, status="tested").count(), len(records))

    def test_parent_can_view_but_not_edit(self):
        from people.models import Student
        child = Student.objects.filter(guardian__user__username="parent1").first()
        parent = self.client_for("parent1")
        r = parent.get(f"/api/hifz/students/{child.id}/programs/")
        self.assertEqual(r.status_code, 200)
        self.assertFalse(r.data["can_edit"])
        self.assertEqual(parent.post(f"/api/hifz/students/{child.id}/tarjuma/", {"surah": 1, "status": "tested"}, format="json").status_code, 403)
        other = Student.objects.exclude(id__in=Student.objects.filter(guardian__user__username="parent1")).first()
        self.assertEqual(parent.get(f"/api/hifz/students/{other.id}/programs/").status_code, 403)


class BiometricTests(DemoDataTestCase):
    def setUp(self):
        from attendance.models import BiometricDevice, BiometricEnrollment
        self.device = BiometricDevice.objects.create(name="Test gate", serial_number="TESTSN1", audience="both")
        self.teacher = User.objects.get(username="qari.yusuf")
        self.pin = BiometricEnrollment.objects.get(user=self.teacher).pin
        self.day = timezone.localdate() - timedelta(days=1)
        while self.day.weekday() == 6:
            self.day -= timedelta(days=1)
        from attendance.models import StaffAttendance
        StaffAttendance.objects.filter(employee__user=self.teacher, date=self.day).delete()

    def test_zk_push_handshake_and_attlog(self):
        from attendance.models import BiometricPunch, StaffAttendance
        c = APIClient()
        r = c.get("/iclock/cdata?SN=TESTSN1&options=all")
        self.assertEqual(r.status_code, 200)
        self.assertIn("GET OPTION FROM: TESTSN1", r.content.decode())
        self.assertEqual(c.get("/iclock/cdata?SN=UNKNOWN&options=all").status_code, 403)
        body = f"{self.pin}\t{self.day} 07:10:00\t0\t1\t0\n{self.pin}\t{self.day} 13:45:00\t1\t1\t0\n"
        r = c.generic("POST", "/iclock/cdata?SN=TESTSN1&table=ATTLOG&Stamp=1", body, content_type="text/plain")
        self.assertEqual(r.content.decode(), "OK: 2")
        rec = StaffAttendance.objects.get(employee__user=self.teacher, date=self.day)
        self.assertEqual((rec.source, str(rec.check_in), str(rec.check_out)), ("device", "07:10:00", "13:45:00"))
        self.assertEqual(rec.status, "present")  # duty starts 07:15 in the demo data
        # re-sending the same log is ignored (deduplicated)
        c.generic("POST", "/iclock/cdata?SN=TESTSN1&table=ATTLOG", body, content_type="text/plain")
        self.assertEqual(BiometricPunch.objects.filter(device=self.device, pin=self.pin).count(), 2)
        self.assertEqual(c.get("/iclock/getrequest?SN=TESTSN1").content.decode(), "OK")

    def test_late_detection_and_student_punch(self):
        from attendance.models import StaffAttendance, StudentAttendance
        from people.models import Student
        st = Student.objects.filter(user__biometric__isnull=False).first()
        StudentAttendance.objects.filter(student=st, date=self.day).delete()
        r = APIClient().post("/api/biometric/punches/", {"punches": [
            {"pin": self.pin, "time": f"{self.day}T08:05:00"},
            {"pin": st.user.biometric.pin, "time": f"{self.day}T07:20:00"}]}, format="json", HTTP_X_DEVICE_KEY=self.device.api_key)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["applied"], 2)
        self.assertEqual(StaffAttendance.objects.get(employee__user=self.teacher, date=self.day).status, "late")
        self.assertEqual(StudentAttendance.objects.get(student=st, date=self.day, subject=None).status, "present")
        self.assertEqual(APIClient().post("/api/biometric/punches/", {"punches": [{"pin": "1", "time": "2026-01-01 08:00"}]},
                                          format="json", HTTP_X_DEVICE_KEY="wrong").status_code, 401)

    def test_leave_is_not_overwritten(self):
        from attendance.models import StaffAttendance
        StaffAttendance.objects.create(employee=self.teacher.employee_profile, date=self.day, status="leave", source="leave")
        r = APIClient().post("/api/biometric/punches/", {"punches": [{"pin": self.pin, "time": f"{self.day} 07:00"}]},
                             format="json", HTTP_X_DEVICE_KEY=self.device.api_key)
        self.assertEqual(r.data["skipped"], 1)
        self.assertEqual(StaffAttendance.objects.get(employee__user=self.teacher, date=self.day).status, "leave")

    def test_csv_import_unknown_pin_then_enrol(self):
        from django.core.files.uploadedfile import SimpleUploadedFile

        from attendance.models import BiometricEnrollment, BiometricPunch, StaffAttendance
        BiometricEnrollment.objects.filter(user=self.teacher).delete()
        csv = f"AC-No.,Name,Time,State\n777,Yusuf,{self.day:%d/%m/%Y} 07:01:00,C/In\n777,Yusuf,{self.day:%d/%m/%Y} 13:30:00,C/Out\n"
        hr = self.client_for("hr")
        r = hr.post("/api/biometric/import/", {"file": SimpleUploadedFile("log.csv", csv.encode())}, format="multipart")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(r.data["unmatched"], 2)
        r = hr.post("/api/biometric-enrollments/", {"user": self.teacher.id, "pin": "777"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        self.assertEqual(BiometricPunch.objects.filter(pin="777", result="applied").count(), 2)
        self.assertEqual(str(StaffAttendance.objects.get(employee__user=self.teacher, date=self.day).check_out), "13:30:00")

    def test_close_day_marks_absent_and_permissions(self):
        from attendance.models import StaffAttendance
        hr = self.client_for("hr")
        r = hr.post("/api/biometric/close-day/", {"date": str(self.day), "staff": True}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(StaffAttendance.objects.get(employee__user=self.teacher, date=self.day).status, "absent")
        self.assertEqual(self.client_for("qari.yusuf").post("/api/biometric/close-day/", {"date": str(self.day)}, format="json").status_code, 403)
        self.assertEqual(hr.get("/api/biometric/status/").status_code, 200)


class WebsiteApiTests(DemoDataTestCase):
    """The React public website's API (/api/site/public/) and the online admission flow."""

    def test_read_endpoints(self):
        c = APIClient()
        for url in ["settings", "home", "programs", "departments", "faculty", "news", "events", "announcements", "calendar",
                    "gallery", "documents", "merit-lists", "testimonials", "faqs", "pages/rules-and-regulations", "search?q=quran"]:
            r = c.get(f"/api/site/public/{url}")
            self.assertEqual(r.status_code, 200, url)
            self.assertTrue(r.json()["success"], url)
        prog = c.get("/api/site/public/programs").json()["data"][0]
        self.assertEqual(c.get(f"/api/site/public/programs/{prog['slug']}").status_code, 200)
        self.assertEqual(c.get("/api/site/public/programs/does-not-exist").status_code, 404)
        faculty = c.get("/api/site/public/faculty").json()["data"][0]
        self.assertNotIn("phone", faculty)

    def _application(self, program_id, cnic="3520212345671"):
        import json
        from django.core.files.uploadedfile import SimpleUploadedFile
        data = {"personal": {"fullName": "Test Talib", "cnic": cnic, "dateOfBirth": "2008-04-01", "gender": "male",
                             "phone": "03001234567", "address": "House 1, Street 2", "city": "Lahore", "fatherName": "Test Father",
                             "fatherCnic": "3520276543211"},
                "qualification": "Matric", "education": [{"level": "matric", "totalMarks": "1100", "obtainedMarks": "990"}],
                "program": str(program_id), "residence": "boarding", "declarationAccepted": True, "rulesAccepted": True,
                "session": "2026-2027"}
        f = lambda n: SimpleUploadedFile(n, b"%PDF-1.4 test", content_type="application/pdf")  # noqa: E731
        return {"data": json.dumps(data), "photo": SimpleUploadedFile("p.png", b"\x89PNG", content_type="image/png"),
                "cnic": f("c.pdf"), "guardianCnic": f("g.pdf")}

    def test_admission_submit_track_and_merit(self):
        from cms.models import MeritList, Program
        from people.models import AdmissionApplication
        c = APIClient()
        prog = Program.objects.get(code="DN")
        r = c.post("/api/site/public/admissions", self._application(prog.pk), format="multipart")
        self.assertEqual(r.status_code, 201, r.content)
        number = r.json()["data"]["applicationNumber"]
        self.assertTrue(number.startswith("UMS-"))
        app = AdmissionApplication.objects.get(application_no=number)
        self.assertEqual((app.source, float(app.aggregate), app.documents.count()), ("website", 90.0, 3))
        # duplicate and invalid submissions
        self.assertEqual(c.post("/api/site/public/admissions", self._application(prog.pk), format="multipart").status_code, 409)
        bad = c.post("/api/site/public/admissions", {"data": "{}"}, format="multipart")
        self.assertEqual(bad.status_code, 400)
        self.assertTrue(any(e["field"] == "personal.cnic" for e in bad.json()["errors"]))
        # tracking needs the matching CNIC
        self.assertEqual(c.post("/api/site/public/admissions/track", {"applicationNumber": number, "cnic": "1"}, format="json").status_code, 404)
        t = c.post("/api/site/public/admissions/track", {"applicationNumber": number, "cnic": "35202-1234567-1"}, format="json").json()["data"]
        self.assertEqual(t["status"], "submitted")
        # status change shows in the timeline; "accepted" is shown as "approved"
        app.status = "accepted"
        app.save()
        t = c.post("/api/site/public/admissions/track", {"applicationNumber": number, "cnic": "3520212345671"}, format="json").json()["data"]
        self.assertEqual([h["status"] for h in t["timeline"]], ["submitted", "approved"])
        # merit list generation from the portal ranks by aggregate
        staff = self.client_for("admin")
        ml = MeritList.objects.create(title="Test list", program=prog, session="2026-2027")
        r = staff.post(f"/api/merit-lists/{ml.pk}/generate/", {}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertEqual(ml.entries.first().application_number, number)

    def test_contact_and_content_management(self):
        c = APIClient()
        self.assertEqual(c.post("/api/site/public/contact", {"name": "A"}, format="json").status_code, 400)
        r = c.post("/api/site/public/contact", {"name": "Ali", "email": "a@example.com", "subject": "Hello",
                                                "message": "Is boarding available?"}, format="json")
        self.assertEqual(r.status_code, 201)
        staff = self.client_for("admin")
        r = staff.post("/api/web-news/", {"title": "Jalsa held", "content": "Alhamdulillah."}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        slug = r.json()["slug"]
        self.assertEqual(APIClient().get(f"/api/site/public/news/{slug}").json()["data"]["title"], "Jalsa held")
        # students cannot edit website content
        self.assertEqual(self.client_for(User.objects.filter(role=R.STUDENT).first().username)
                         .post("/api/web-news/", {"title": "x", "content": "y"}, format="json").status_code, 403)
