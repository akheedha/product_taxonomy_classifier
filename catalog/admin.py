from django.contrib import admin
from django.utils.html import format_html
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'product_number',
        'product_name',
        'product_category',
        'product_sub_category',
        'product_color',
        'item_cost',
        'msrp',
        'image_count_display',
    )
    list_filter = (
        'product_category',
        'assembly_required',
        'is_set',
        'stackable',
        'country_of_origin',
    )
    search_fields = (
        'product_number',
        'model_number',
        'product_name',
        'collection_name',
        'product_category',
        'product_sub_category',
    )
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    fieldsets = (
        ("Identification", {
            "fields": (
                "product_number",
                "model_number",
                "product_name",
                "collection_name",
                "color_collection",
                "product_color",
            )
        }),
        ("Categorization", {
            "fields": (
                "product_category",
                "product_sub_category",
            )
        }),
        ("Pricing", {
            "fields": (
                "item_cost",
                "map_price",
                "msrp",
            )
        }),
        ("Content & Details", {
            "fields": (
                "product_description",
                "bullets",
                "set_includes",
                "materials",
                "product_dimensions",
                "product_weight",
                "assembly_required",
                "is_set",
                "stackable",
                "country_of_origin",
            )
        }),
        ("Shipping & Packaging", {
            "fields": (
                "shipping_method",
                "total_box_count",
                "pallet_count",
                "shipping_weight",
                "total_cbm",
                "package_dimensions",
            )
        }),
        ("Media & Links", {
            "fields": (
                "product_url",
                "images",
                "image_preview",
            )
        }),
        ("Metadata", {
            "fields": (
                "created_at",
                "updated_at",
            )
        }),
    )

    @admin.display(description="Images")
    def image_count_display(self, obj):
        count = obj.image_count
        return f"{count} img{'s' if count != 1 else ''}"

    @admin.display(description="Image Preview")
    def image_preview(self, obj):
        if not obj.images:
            return "No images available"
        html = '<div style="display: flex; gap: 8px; flex-wrap: wrap;">'
        for img in obj.images[:5]:
            html += f'<img src="{img}" style="height: 80px; width: 80px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />'
        html += '</div>'
        return format_html(html)
