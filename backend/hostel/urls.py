from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("hostels", views.HostelViewSet)
router.register("hostel-rooms", views.HostelRoomViewSet)
router.register("hostel-allocations", views.HostelAllocationViewSet)
router.register("mess-menu", views.MessMenuViewSet)
router.register("gate-passes", views.GatePassViewSet)
router.register("roll-calls", views.RollCallViewSet)

urlpatterns = [
    path("hostel/roll-call/", views.RollCallSheetView.as_view()),
    path("hostel/occupancy/", views.OccupancyView.as_view()),
    *router.urls,
]
