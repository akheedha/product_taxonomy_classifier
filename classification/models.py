"""
================================================================================
CLASSIFICATION JOBS & RESULTS MODELS
================================================================================
Purpose:
  Persists background classification runs and prediction outputs:
    1. ClassificationJob: Represents a batch processing run (total items, processed count,
       timing, status, failure counts).
    2. ClassificationResult: Stores individual product prediction outcomes (predicted Shopify
       category, confidence score, alternative categories, extracted attributes, needs_manual_review
       flag, and curator approval/override state).
"""

from django.db import models


class ClassificationJob(models.Model):
    """
    Tracks batch or async taxonomy classification job runs.
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


class ClassificationResult(models.Model):
    """
    Stores classification outputs for a single product within a job run,
    including predicted taxonomy category, confidence score, alternatives,
    and extracted attributes.
    """
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        DONE = 'done', 'Done'
        FAILED = 'failed', 'Failed'

    product = models.ForeignKey(
        'catalog.Product',
        on_delete=models.CASCADE,
        related_name='classification_results',
        help_text="Product that was classified"
    )
    job = models.ForeignKey(
        ClassificationJob,
        on_delete=models.CASCADE,
        related_name='results',
        help_text="Classification job run"
    )
    predicted_category = models.ForeignKey(
        'taxonomy.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='classification_predictions',
        help_text="Primary predicted Shopify taxonomy category"
    )
    confidence = models.FloatField(
        default=0.0,
        db_index=True,
        help_text="Prediction confidence score (0.0 to 1.0)"
    )
    alternative_categories = models.JSONField(
        default=list,
        blank=True,
        help_text="Alternative top-K predicted categories: list of {category_id, name, score}"
    )
    extracted_attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Extracted attributes dictionary: {attribute_name: {value, confidence}}"
    )
    needs_manual_review = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flag indicating confidence is below threshold or ambiguity requires human review"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Result processing state"
    )
    error_message = models.TextField(
        null=True,
        blank=True,
        help_text="Error details if classification failed"
    )
    reviewed_by = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Username of human reviewer who inspected/approved this result"
    )
    approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this classification is approved for export"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Classification Result'
        verbose_name_plural = 'Classification Results'
        ordering = ['-updated_at']
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'job'],
                name='unique_product_job_result'
            )
        ]
        indexes = [
            models.Index(
                fields=['needs_manual_review', 'status'],
                name='idx_review_status'
            ),
            models.Index(
                fields=['job', 'status'],
                name='idx_job_status'
            ),
        ]

    def __str__(self):
        cat_name = self.predicted_category.name if self.predicted_category else "Unclassified"
        return f"{self.product.product_number} -> {cat_name} ({self.confidence:.2f})"
