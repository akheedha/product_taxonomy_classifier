"""
================================================================================
CELERY ASYNCHRONOUS TASKS FOR TAXONOMY CLASSIFICATION
================================================================================
Purpose:
  Executes large-scale batch product classification in background worker processes
  without blocking the web request cycle or freezing the user interface.

Features:
  - Batch Chunking: Processes items in manageable sub-batches (default 100).
  - Resumable Execution: If interrupted, skips products already marked 'DONE'.
  - Real-time Progress Tracking: Flushes processed counts to the database every 5 items.
  - Per-Product Fault Tolerance: Any individual product classification failure is caught,
    logged, and saved as a 'FAILED' record without halting the rest of the job.
"""

import logging
from typing import Any, Dict, List, Optional
from celery import shared_task
from django.db import transaction
from django.utils import timezone

from .engine.fusion import classify_product
from .models import ClassificationJob, ClassificationResult
from catalog.models import Product

logger = logging.getLogger(__name__)

# Number of products processed before performing batch checkpointing
BATCH_SIZE = 100


@shared_task(bind=True, name='classification.tasks.process_classification_job')
def process_classification_job(self, job_id: int) -> Dict[str, Any]:
    """
    Background worker task to classify all products assigned to a ClassificationJob.

    Workflow:
      1. Loads ClassificationJob from DB and marks status as RUNNING with timestamp.
      2. Finds all target products (or pending items not yet completed).
      3. Iterates through products in chunks of 100:
         a. Runs multimodal fusion classifier (SentenceTransformers + OpenCLIP + RapidFuzz).
         b. Updates/creates the ClassificationResult record with predicted category, confidence, and attributes.
         c. Periodically flushes `job.processed_count` to DB for real-time frontend dashboard polling.
      4. Marks the job COMPLETED upon finishing all items.

    Args:
        job_id: Primary key (ID) of the ClassificationJob instance.

    Returns:
        Summary dict containing job ID, status, total, processed, and failed counts.
    """
    try:
        job = ClassificationJob.objects.get(id=job_id)
    except ClassificationJob.DoesNotExist:
        logger.error(f"ClassificationJob #{job_id} does not exist.")
        return {"status": "error", "message": f"Job #{job_id} not found"}

    # Update job state to RUNNING
    if job.status != ClassificationJob.Status.RUNNING:
        job.status = ClassificationJob.Status.RUNNING
        if not job.started_at:
            job.started_at = timezone.now()
        job.save(update_fields=['status', 'started_at'])

    logger.info(f"Starting execution of ClassificationJob #{job.id} (total: {job.total_products})...")

    # Step 1: Identify all products targeted for this job
    job_results = ClassificationResult.objects.filter(job=job)

    if job_results.exists():
        # Resumable support: Skip items already successfully classified
        done_product_ids = set(
            job_results.filter(status=ClassificationResult.Status.DONE).values_list('product_id', flat=True)
        )
        pending_product_ids = list(
            job_results.exclude(status=ClassificationResult.Status.DONE).values_list('product_id', flat=True)
        )
        products = list(Product.objects.filter(id__in=pending_product_ids))
    else:
        done_product_ids = set()
        product_limit = job.total_products if job.total_products > 0 else None
        if product_limit:
            products = list(Product.objects.all()[:product_limit])
        else:
            products = list(Product.objects.all())

        if job.total_products == 0:
            job.total_products = len(products)
            job.save(update_fields=['total_products'])

    logger.info(
        f"Job #{job.id}: {len(done_product_ids)} already done, {len(products)} pending processing."
    )

    # Step 2: Split pending products into chunks of 100
    for i in range(0, len(products), BATCH_SIZE):
        batch = products[i:i + BATCH_SIZE]
        logger.info(f"Processing batch {i // BATCH_SIZE + 1} ({len(batch)} products) for Job #{job.id}...")

        for idx, product in enumerate(batch, 1):
            try:
                # Run multimodal fusion engine (Text + Image + Attributes)
                res = classify_product(product)

                # Persist classification output
                ClassificationResult.objects.update_or_create(
                    product=product,
                    job=job,
                    defaults={
                        'predicted_category': res.get('predicted_category'),
                        'confidence': res.get('confidence', 0.0),
                        'alternative_categories': res.get('alternative_categories', []),
                        'extracted_attributes': res.get('extracted_attributes', {}),
                        'needs_manual_review': res.get('needs_manual_review', False),
                        'status': ClassificationResult.Status.DONE,
                        'error_message': None,
                    }
                )
            except Exception as exc:
                logger.exception(f"Classification failed for product {product.product_number}: {exc}")
                ClassificationResult.objects.update_or_create(
                    product=product,
                    job=job,
                    defaults={
                        'status': ClassificationResult.Status.FAILED,
                        'error_message': str(exc),
                    }
                )
                job.failed_count += 1

            # Update and save count frequently (every 5 items or on batch boundary)
            if idx % 5 == 0 or idx == len(batch):
                job.processed_count = ClassificationResult.objects.filter(
                    job=job,
                    status__in=[ClassificationResult.Status.DONE, ClassificationResult.Status.FAILED]
                ).count()
                job.save(update_fields=['processed_count', 'failed_count'])

    # Step 3: Complete Job and record final metrics
    job.refresh_from_db()
    job.status = ClassificationJob.Status.COMPLETED
    job.finished_at = timezone.now()
    job.processed_count = ClassificationResult.objects.filter(
        job=job,
        status__in=[ClassificationResult.Status.DONE, ClassificationResult.Status.FAILED]
    ).count()
    job.save(update_fields=['status', 'finished_at', 'processed_count', 'failed_count'])

    logger.info(
        f"ClassificationJob #{job.id} finished successfully! "
        f"Processed: {job.processed_count}/{job.total_products}, Failed: {job.failed_count}"
    )

    return {
        "job_id": job.id,
        "status": job.status,
        "total_products": job.total_products,
        "processed_count": job.processed_count,
        "failed_count": job.failed_count,
    }
