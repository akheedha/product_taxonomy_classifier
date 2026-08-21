"""
Catalog import audit and execution history model.
"""

from django.db import models


class CatalogImport(models.Model):
    """
    Tracks uploaded catalog files, parsing metrics, and data quality results.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        PARTIAL = 'partial', 'Partial Success'
        FAILED = 'failed', 'Failed'

    filename = models.CharField(max_length=255, help_text="Original uploaded filename")
    sheet_name = models.CharField(max_length=100, null=True, blank=True, help_text="Sheet name or index")
    total_rows = models.PositiveIntegerField(default=0)
    imported_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    data_quality_metrics = models.JSONField(
        default=dict,
        blank=True,
        help_text="Data quality stats (missing descriptions, images, prices)"
    )
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Catalog Import'
        verbose_name_plural = 'Catalog Imports'

    def __str__(self):
        return f"Import #{self.id} ({self.filename}) - {self.imported_count}/{self.total_rows} items"
