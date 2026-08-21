"""
Batch processing job models.
"""

from django.db import models


class ClassificationJob(models.Model):
    """
    Tracks batch background processing job runs, progress, and failure counts.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Job execution status"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    total_products = models.PositiveIntegerField(
        default=0,
        help_text="Total number of products queued in this job"
    )
    processed_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of products processed so far"
    )
    failed_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of products that encountered errors during classification"
    )

    class Meta:
        db_table = 'classification_classificationjob'
        verbose_name = 'Classification Job'
        verbose_name_plural = 'Classification Jobs'
        ordering = ['-created_at']

    def __str__(self):
        return f"Job #{self.id} [{self.get_status_display()}] ({self.processed_count}/{self.total_products})"

    @property
    def progress_percentage(self) -> float:
        if self.total_products > 0:
            return round((self.processed_count / self.total_products) * 100, 1)
        return 0.0

    @property
    def duration_seconds(self) -> float | None:
        if self.started_at and self.finished_at:
            return round((self.finished_at - self.started_at).total_seconds(), 2)
        return None
