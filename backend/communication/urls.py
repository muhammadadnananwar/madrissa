from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("announcements", views.AnnouncementViewSet)
router.register("notifications", views.NotificationViewSet)
router.register("messages", views.MessageViewSet)
router.register("events", views.EventViewSet)
router.register("complaints", views.ComplaintViewSet)
router.register("parent-meetings", views.ParentMeetingViewSet)

urlpatterns = [
    path("communication/feed/", views.FeedView.as_view()),
    path("communication/calendar/", views.CalendarView.as_view()),
    path("communication/recipients/", views.RecipientsView.as_view()),
    *router.urls,
]
