from django.contrib import admin
from .models import ClassificationJob


@admin.register(ClassificationJob)
class ClassificationJobAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'status',
        'progress_percentage',
        'processed_count',
        'total_products',
        'failed_count',
        'created_at',
        'duration_seconds'
    ]
    list_filter = ['status']
    readonly_fields = ['created_at', 'started_at', 'finished_at', 'progress_percentage', 'duration_seconds']
