from django.contrib import admin

from .models import (Asset, AssetCategory, StockItem, StockMovement, Vendor)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone', 'email')
    search_fields = ('name', 'contact_person', 'phone')


@admin.register(AssetCategory)
class AssetCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'tag', 'category', 'room', 'vendor', 'assigned_to')
    search_fields = ('name', 'tag')
    list_filter = ('condition', 'is_waqf')
    list_select_related = ('category', 'room', 'vendor', 'assigned_to')


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'unit', 'quantity', 'reorder_level')
    search_fields = ('name', 'category', 'unit')


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('item', 'kind', 'quantity', 'date', 'vendor', 'unit_cost')
    search_fields = ('issued_to', 'notes')
    list_filter = ('kind',)
    list_select_related = ('item', 'vendor', 'recorded_by')
