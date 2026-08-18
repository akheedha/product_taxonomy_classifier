from django.contrib import admin
from django.utils.html import format_html
from .models import ClassificationJob, ClassificationResult


class ClassificationResultInline(admin.TabularInline):
    model = ClassificationResult
    extra = 0
    show_change_link = True
    fields = ('product', 'predicted_category', 'confidence', 'needs_manual_review', 'status', 'approved')
    readonly_fields = ('product', 'predicted_category', 'confidence', 'needs_manual_review', 'status', 'approved')
    can_delete = False
    max_num = 10


@admin.register(ClassificationJob)
class ClassificationJobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'status_badge',
        'progress_display',
        'total_products',
        'processed_count',
        'failed_count',
        'created_at',
        'duration_display',
    )
    list_filter = ('status', 'created_at')
    search_fields = ('id',)
    readonly_fields = (
        'created_at',
        'started_at',
        'finished_at',
        'progress_display',
        'duration_display',
    )
    inlines = [ClassificationResultInline]
    ordering = ['-created_at']

    @admin.display(description="Status", ordering="status")
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'running': '#17a2b8',
            'completed': '#28a745',
            'failed': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display().upper()
        )

    @admin.display(description="Progress")
    def progress_display(self, obj):
        pct = obj.progress_percentage
        return format_html(
            '<div style="width: 120px; background-color: #e9ecef; border-radius: 4px; overflow: hidden; height: 16px; position: relative;">'
            '<div style="width: {}%; background-color: #007bff; height: 100%;"></div>'
            '<span style="position: absolute; width: 100%; top: 0; left: 0; text-align: center; font-size: 10px; line-height: 16px; font-weight: bold;">{}%</span>'
            '</div>',
            pct,
            pct
        )

    @admin.display(description="Duration")
    def duration_display(self, obj):
        duration = obj.duration_seconds
        if duration is not None:
            return f"{duration}s"
        return "-"


@admin.register(ClassificationResult)
class ClassificationResultAdmin(admin.ModelAdmin):
    list_display = (
        'product',
        'job',
        'predicted_category',
        'confidence_badge',
        'needs_manual_review',
        'status',
        'approved',
        'reviewed_by',
        'updated_at',
    )
    list_filter = (
        'needs_manual_review',
        'status',
        'approved',
        'job',
    )
    search_fields = (
        'product__product_number',
        'product__product_name',
        'predicted_category__name',
        'predicted_category__full_name',
        'reviewed_by',
    )
    autocomplete_fields = ('product', 'predicted_category', 'job')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_selected', 'flag_for_review']
    ordering = ['-updated_at']

    @admin.display(description="Confidence", ordering="confidence")
    def confidence_badge(self, obj):
        conf = obj.confidence
        if conf >= 0.8:
            color = "#28a745"  # Green
        elif conf >= 0.5:
            color = "#ffc107"  # Yellow/Orange
        else:
            color = "#dc3545"  # Red
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.2f} ({:.0f}%)</span>',
            color,
            conf,
            conf * 100
        )

    @admin.action(description="Mark selected results as Approved")
    def approve_selected(self, request, queryset):
        rows_updated = queryset.update(
            approved=True,
            needs_manual_review=False,
            reviewed_by=request.user.username or "admin"
        )
        self.message_user(request, f"{rows_updated} classification results marked as approved.")

    @admin.action(description="Flag selected results for Manual Review")
    def flag_for_review(self, request, queryset):
        rows_updated = queryset.update(needs_manual_review=True, approved=False)
        self.message_user(request, f"{rows_updated} classification results flagged for manual review.")
