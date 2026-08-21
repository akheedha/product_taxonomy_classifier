"""
Classification prediction results models.
"""

from django.db import models


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
        'products.Product',
        on_delete=models.CASCADE,
        related_name='classification_results',
        help_text="Product that was classified"
    )
    job = models.ForeignKey(
        'processing.ClassificationJob',
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
        db_table = 'classification_classificationresult'
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
