from django.contrib import admin
from .models import Product, Sale, SaleItem


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    readonly_fields = ['product', 'quantity', 'unit_price', 'total_price']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'barcode', 'price', 'quantity', 'updated_at']
    list_filter = ['created_at']
    search_fields = ['name', 'barcode']
    ordering = ['name']


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ['id', 'total_amount', 'created_at']
    inlines = [SaleItemInline]
    readonly_fields = ['total_amount', 'created_at']
    ordering = ['-created_at']


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'sale', 'product', 'quantity', 'unit_price', 'total_price']
    list_select_related = ['sale', 'product']
