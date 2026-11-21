from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("leave-types", views.LeaveTypeViewSet)
router.register("leave-requests", views.LeaveRequestViewSet)

urlpatterns = [
    path("leaves/balance/", views.LeaveBalanceView.as_view()),
    path("leaves/pending/", views.PendingLeavesView.as_view()),
    path("leaves/today/", views.OnLeaveTodayView.as_view()),
    *router.urls,
]
