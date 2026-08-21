from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'product_number',
        'product_name',
        'brand',
        'product_category',
        'product_sub_category',
        'image_count',
        'created_at',
    ]
    list_filter = ['product_category', 'brand', 'assembly_required', 'is_set']
    search_fields = ['product_number', 'product_name', 'brand', 'materials']
    readonly_fields = ['created_at', 'updated_at', 'image_count']
