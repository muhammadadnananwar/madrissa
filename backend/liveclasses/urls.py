from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("live-classes", views.LiveClassViewSet)
router.register("live-participants", views.LiveClassParticipantViewSet)

urlpatterns = [
    path("liveclasses/upcoming/", views.UpcomingClassesView.as_view()),
    path("liveclasses/recurring/", views.RecurringScheduleView.as_view()),
    path("liveclasses/providers/", views.ProviderStatusView.as_view()),
    *router.urls,
]
