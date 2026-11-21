from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("hifz-records", views.HifzRecordViewSet)
router.register("juz-progress", views.JuzProgressViewSet)
router.register("qaida-lessons", views.QaidaLessonViewSet)
router.register("qaida-progress", views.QaidaProgressViewSet)
router.register("tarjuma-progress", views.TarjumaProgressViewSet)
router.register("khatm-register", views.QuranCompletionViewSet)
router.register("checklist-items", views.ChecklistItemViewSet)
router.register("student-checklist", views.StudentChecklistViewSet)

urlpatterns = [
    path("hifz/daily/", views.DailySheetView.as_view()),
    path("hifz/students/<int:student_id>/", views.StudentHifzSummaryView.as_view()),
    path("hifz/students/<int:student_id>/juz/", views.SetJuzView.as_view()),
    path("hifz/students/<int:student_id>/programs/", views.StudentProgramsView.as_view()),
    path("hifz/students/<int:student_id>/qaida/", views.SetQaidaView.as_view()),
    path("hifz/students/<int:student_id>/tarjuma/", views.SetTarjumaView.as_view()),
    path("hifz/students/<int:student_id>/checklist/", views.SetChecklistView.as_view()),
    path("hifz/students/<int:student_id>/khatm/", views.RecordKhatmView.as_view()),
    path("hifz/checklist-sheet/", views.ChecklistSheetView.as_view()),
    path("hifz/sections/<int:section_id>/", views.SectionHifzOverviewView.as_view()),
    *router.urls,
]
