from rest_framework import serializers

from core.serializers import LabeledModelSerializer

from .models import Asset, AssetCategory, StockItem, StockMovement, Vendor


class VendorSerializer(LabeledModelSerializer):
    class Meta:
        model = Vendor
        fields = "__all__"


class AssetCategorySerializer(LabeledModelSerializer):
    class Meta:
        model = AssetCategory
        fields = "__all__"


class AssetSerializer(LabeledModelSerializer):
    class Meta:
        model = Asset
        fields = "__all__"


class StockItemSerializer(LabeledModelSerializer):
    class Meta:
        model = StockItem
        fields = "__all__"


class StockMovementSerializer(LabeledModelSerializer):
    class Meta:
        model = StockMovement
        fields = "__all__"

    def validate(self, attrs):
        if attrs.get("quantity") is not None and attrs["quantity"] <= 0:
            raise serializers.ValidationError({"quantity": "Must be positive."})
        item = attrs.get("item", getattr(self.instance, "item", None))
        kind = attrs.get("kind", getattr(self.instance, "kind", None))
        if kind == StockMovement.Kind.OUT and item and not self.instance and attrs["quantity"] > item.quantity:
            raise serializers.ValidationError({"quantity": f"Only {item.quantity} {item.unit} in stock."})
        return attrs
