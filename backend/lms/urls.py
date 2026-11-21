from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("courses", views.CourseViewSet)
router.register("course-enrollments", views.CourseEnrollmentViewSet)
router.register("modules", views.ModuleViewSet)
router.register("lessons", views.LessonViewSet)
router.register("assignments", views.AssignmentViewSet)
router.register("submissions", views.SubmissionViewSet)
router.register("quizzes", views.QuizViewSet)
router.register("questions", views.QuestionViewSet)
router.register("choices", views.ChoiceViewSet)
router.register("quiz-attempts", views.QuizAttemptViewSet)
router.register("discussion-threads", views.DiscussionThreadViewSet)
router.register("discussion-replies", views.DiscussionReplyViewSet)
router.register("homework", views.HomeworkViewSet)

urlpatterns = [
    path("lms/my-courses/", views.MyCoursesView.as_view()),
    path("lms/my-tasks/", views.MyTasksView.as_view()),
    path("lms/threads/<int:pk>/", views.ThreadDetailView.as_view()),
    path("lms/courses/<int:course_id>/threads/", views.CourseThreadsView.as_view()),
    *router.urls,
]
