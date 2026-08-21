from django.contrib import admin
from .models import CatalogImport


@admin.register(CatalogImport)
class CatalogImportAdmin(admin.ModelAdmin):
    list_display = ['id', 'filename', 'sheet_name', 'total_rows', 'imported_count', 'skipped_count', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['filename']
    readonly_fields = ['created_at', 'data_quality_metrics']
