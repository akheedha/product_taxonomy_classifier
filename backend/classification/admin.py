from django.contrib import admin
from .models import ClassificationResult


@admin.register(ClassificationResult)
class ClassificationResultAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'product',
        'job',
        'predicted_category',
        'confidence',
        'needs_manual_review',
        'approved',
        'status',
        'created_at',
    ]
    list_filter = ['needs_manual_review', 'approved', 'status', 'job']
    search_fields = ['product__product_number', 'product__product_name', 'predicted_category__name']
    readonly_fields = ['created_at', 'updated_at']
