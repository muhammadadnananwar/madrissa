from django.db.models import F
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from core.roles import INVENTORY, R, has_role
from core.viewsets import BaseModelViewSet

from . import serializers as s
from .models import Asset, AssetCategory, StockItem, StockMovement, Vendor

G = "Inventory & Assets"


class VendorViewSet(BaseModelViewSet):
    queryset = Vendor.objects.all()
    serializer_class = s.VendorSerializer
    resource_key = "vendors"
    read_roles = write_roles = INVENTORY + [R.ACCOUNTANT]
    search_fields = ["name", "phone"]
    label, group, icon = "Vendors / Suppliers", G, "truck"
    list_fields = ["name", "contact_person", "phone", "email"]


class AssetCategoryViewSet(BaseModelViewSet):
    queryset = AssetCategory.objects.all()
    serializer_class = s.AssetCategorySerializer
    resource_key = "asset-categories"
    read_roles = write_roles = INVENTORY
    group, icon = G, "folder"
    list_fields = ["name"]


class AssetViewSet(BaseModelViewSet):
    queryset = Asset.objects.all()
    serializer_class = s.AssetSerializer
    resource_key = "assets"
    read_roles, write_roles = INVENTORY + [R.ACCOUNTANT], INVENTORY
    search_fields = ["name", "tag"]
    filterset_fields = ["category", "room", "condition", "is_waqf", "assigned_to"]
    group, icon = G, "box"
    list_fields = ["tag", "name", "category", "room", "assigned_to", "condition", "cost", "is_waqf"]


class StockItemViewSet(BaseModelViewSet):
    queryset = StockItem.objects.all()
    serializer_class = s.StockItemSerializer
    resource_key = "stock-items"
    read_roles, write_roles = INVENTORY + [R.HOSTEL_WARDEN], INVENTORY
    search_fields = ["name", "category"]
    label, group, icon = "Stock Items", G, "archive"
    list_fields = ["name", "category", "quantity", "unit", "reorder_level"]


class StockMovementViewSet(BaseModelViewSet):
    queryset = StockMovement.objects.all()
    serializer_class = s.StockMovementSerializer
    resource_key = "stock-movements"
    read_roles = write_roles = INVENTORY + [R.HOSTEL_WARDEN]
    filterset_fields = ["item", "kind", "date", "vendor"]
    label, group, icon = "Stock In / Out", G, "swap"
    list_fields = ["date", "item", "kind", "quantity", "issued_to", "vendor", "recorded_by"]


class LowStockView(APIView):
    def get(self, request):
        if not has_role(request.user, INVENTORY + [R.HOSTEL_WARDEN]):
            raise PermissionDenied()
        return Response([{"id": x.id, "name": x.name, "quantity": x.quantity, "unit": x.unit, "reorder_level": x.reorder_level}
                         for x in StockItem.objects.filter(quantity__lte=F("reorder_level"))])
