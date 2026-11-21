from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("students", views.StudentViewSet)
router.register("employees", views.EmployeeViewSet)
router.register("guardians", views.GuardianViewSet)
router.register("admissions", views.AdmissionApplicationViewSet)
router.register("admission-documents", views.AdmissionDocumentViewSet)
router.register("promotions", views.StudentPromotionViewSet)
router.register("qualifications", views.QualificationViewSet)
router.register("employment-history", views.EmploymentHistoryViewSet)
router.register("documents", views.PersonDocumentViewSet)
router.register("disciplinary", views.DisciplinaryRecordViewSet)
router.register("medical", views.MedicalRecordViewSet)
router.register("achievements", views.AchievementViewSet)
router.register("visitors", views.VisitorLogViewSet)

urlpatterns = [
    path("people/promote/", views.PromoteView.as_view()),
    path("people/profile/<int:user_id>/", views.Profile360View.as_view()),
    path("people/my-children/", views.MyChildrenView.as_view()),
    path("people/sections/<int:section_id>/roster/", views.SectionRosterView.as_view()),
    *router.urls,
]
