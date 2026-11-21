from django.conf import settings
from django.db import models
from django.db.models import F
from django.utils import timezone

from academics.models import Room
from core.models import TimeStamped

User = settings.AUTH_USER_MODEL


class Vendor(TimeStamped):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)

    def __str__(self):
        return self.name


class AssetCategory(TimeStamped):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name_plural = "asset categories"

    def __str__(self):
        return self.name


class Asset(TimeStamped):
    class Condition(models.TextChoices):
        NEW = "new", "New"
        GOOD = "good", "Good"
        NEEDS_REPAIR = "repair", "Needs repair"
        DAMAGED = "damaged", "Damaged"
        DISPOSED = "disposed", "Disposed"

    name = models.CharField(max_length=150)
    tag = models.CharField("Asset tag", max_length=40, unique=True)
    category = models.ForeignKey(AssetCategory, null=True, blank=True, on_delete=models.SET_NULL)
    room = models.ForeignKey(Room, null=True, blank=True, on_delete=models.SET_NULL)
    vendor = models.ForeignKey(Vendor, null=True, blank=True, on_delete=models.SET_NULL)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assets")
    purchase_date = models.DateField(null=True, blank=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    condition = models.CharField(max_length=10, choices=Condition.choices, default=Condition.GOOD)
    is_waqf = models.BooleanField(default=False, help_text="Donated as waqf")
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.tag} {self.name}"


class StockItem(TimeStamped):
    name = models.CharField(max_length=150, help_text="e.g. Rice, Chalk, Registers, Quran copies")
    category = models.CharField(max_length=60, blank=True)
    unit = models.CharField(max_length=20, default="pcs")
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0, editable=False)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.quantity} {self.unit})"


class StockMovement(TimeStamped):
    class Kind(models.TextChoices):
        IN = "in", "Stock in (purchase / donation)"
        OUT = "out", "Stock out (issue / consumption)"

    item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name="movements")
    kind = models.CharField(max_length=3, choices=Kind.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    vendor = models.ForeignKey(Vendor, null=True, blank=True, on_delete=models.SET_NULL)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    issued_to = models.CharField(max_length=150, blank=True)
    notes = models.CharField(max_length=200, blank=True)
    recorded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"{self.get_kind_display()} {self.quantity} {self.item.name}"

    def _delta(self):
        return self.quantity if self.kind == self.Kind.IN else -self.quantity

    def save(self, *args, **kwargs):
        if self.pk:
            old = StockMovement.objects.get(pk=self.pk)
            StockItem.objects.filter(pk=old.item_id).update(quantity=F("quantity") - old._delta())
        super().save(*args, **kwargs)
        StockItem.objects.filter(pk=self.item_id).update(quantity=F("quantity") + self._delta())

    def delete(self, *args, **kwargs):
        StockItem.objects.filter(pk=self.item_id).update(quantity=F("quantity") - self._delta())
        super().delete(*args, **kwargs)
