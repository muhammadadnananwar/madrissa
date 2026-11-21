from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("student-attendance", views.StudentAttendanceViewSet)
router.register("staff-attendance", views.StaffAttendanceViewSet)
router.register("biometric-devices", views.BiometricDeviceViewSet)
router.register("biometric-enrollments", views.BiometricEnrollmentViewSet)
router.register("biometric-punches", views.BiometricPunchViewSet)

urlpatterns = [
    path("attendance/sheet/", views.AttendanceSheetView.as_view()),
    path("attendance/bulk/", views.BulkMarkView.as_view()),
    path("attendance/staff/self/", views.StaffSelfView.as_view()),
    path("attendance/staff/sheet/", views.StaffSheetView.as_view()),
    path("attendance/staff/bulk/", views.StaffBulkView.as_view()),
    path("attendance/report/", views.AttendanceReportView.as_view()),
    path("attendance/register/", views.MonthlyRegisterView.as_view()),
    path("attendance/mine/", views.MyAttendanceView.as_view()),
    path("attendance/overview/", views.TodayOverviewView.as_view()),
    path("biometric/status/", views.BiometricStatusView.as_view()),
    path("biometric/import/", views.BiometricImportView.as_view()),
    path("biometric/process/", views.BiometricProcessView.as_view()),
    path("biometric/close-day/", views.BiometricCloseDayView.as_view()),
    path("biometric/auto-enroll/", views.BiometricAutoEnrollView.as_view()),
    path("biometric/punches/", views.DevicePunchAPIView.as_view()),
    *router.urls,
]
