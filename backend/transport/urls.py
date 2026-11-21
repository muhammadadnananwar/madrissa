from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("vehicles", views.VehicleViewSet)
router.register("routes", views.RouteViewSet)
router.register("route-stops", views.RouteStopViewSet)
router.register("transport-assignments", views.TransportAssignmentViewSet)

urlpatterns = router.urls
