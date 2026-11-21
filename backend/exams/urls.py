from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("grade-scales", views.GradeScaleViewSet)
router.register("exams", views.ExamViewSet)
router.register("exam-papers", views.ExamPaperViewSet)
router.register("marks", views.MarkViewSet)
router.register("certificates", views.CertificateViewSet)

urlpatterns = [
    path("exams/papers/<int:paper_id>/marks/", views.MarksSheetView.as_view()),
    path("exams/result/", views.SectionResultView.as_view()),
    path("exams/report-card/", views.ReportCardView.as_view()),
    path("exams/mine/", views.MyExamsView.as_view()),
    path("exams/certificates/<int:pk>/print/", views.CertificatePrintView.as_view()),
    *router.urls,
]
