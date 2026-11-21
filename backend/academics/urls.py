from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("academic-years", views.AcademicYearViewSet)
router.register("departments", views.DepartmentViewSet)
router.register("class-levels", views.ClassLevelViewSet)
router.register("sections", views.SectionViewSet)
router.register("subjects", views.SubjectViewSet)
router.register("rooms", views.RoomViewSet)
router.register("teacher-assignments", views.TeacherAssignmentViewSet)
router.register("time-slots", views.TimeSlotViewSet)
router.register("timetable", views.TimetableEntryViewSet)
router.register("holidays", views.HolidayViewSet)
router.register("syllabus", views.SyllabusViewSet)

urlpatterns = [
    path("academics/timetable-view/", views.TimetableGridView.as_view()),
    path("academics/my-sections/", views.MySectionsView.as_view()),
    path("academics/sections/<int:section_id>/subjects/", views.SectionSubjectsView.as_view()),
    *router.urls,
]
