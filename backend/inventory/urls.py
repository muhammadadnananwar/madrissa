from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter()
router.register("vendors", views.VendorViewSet)
router.register("asset-categories", views.AssetCategoryViewSet)
router.register("assets", views.AssetViewSet)
router.register("stock-items", views.StockItemViewSet)
router.register("stock-movements", views.StockMovementViewSet)

urlpatterns = [path("inventory/low-stock/", views.LowStockView.as_view()), *router.urls]
