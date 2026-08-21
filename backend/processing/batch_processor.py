"""
Batch processing engine with chunking, atomic checkpointing, and per-item fault isolation.
"""

import logging
from typing import Dict, Any, List, Optional
from django.utils import timezone
from products.models import Product
from classification.models import ClassificationResult
from classification.engine.fusion import classify_product
from .models import ClassificationJob

logger = logging.getLogger(__name__)


class BatchProcessor:
    """
    Executes large-scale batch product classification with resumable state,
    chunking, and per-item fault isolation.
    """

    @classmethod
    def process_job(cls, job_id: int, chunk_size: int = 100) -> Dict[str, Any]:
        try:
            job = ClassificationJob.objects.get(id=job_id)
        except ClassificationJob.DoesNotExist:
            logger.error(f"ClassificationJob #{job_id} not found.")
            return {"status": "error", "message": f"Job #{job_id} not found"}

        # Mark job as RUNNING
        if job.status != ClassificationJob.Status.RUNNING:
            job.status = ClassificationJob.Status.RUNNING
            if not job.started_at:
                job.started_at = timezone.now()
            job.save(update_fields=['status', 'started_at'])

        logger.info(f"Processing Batch Job #{job.id} (total: {job.total_products})...")

        # Resumability check: exclude products already marked DONE
        done_product_ids = set(
            ClassificationResult.objects.filter(job=job, status=ClassificationResult.Status.DONE).values_list('product_id', flat=True)
        )

        limit = job.total_products if job.total_products > 0 else None
        if limit:
            all_products = list(Product.objects.all()[:limit])
        else:
            all_products = list(Product.objects.all())

        if job.total_products == 0:
            job.total_products = len(all_products)
            job.save(update_fields=['total_products'])

        # Queue only pending products
        products = [p for p in all_products if p.id not in done_product_ids]

        logger.info(f"Job #{job.id}: {len(done_product_ids)} already done, {len(products)} pending processing.")

        # Chunked iteration
        for i in range(0, len(products), chunk_size):
            chunk = products[i:i + chunk_size]
            for idx, product in enumerate(chunk, 1):
                cls._process_single_product(product, job)

                # Periodic checkpointing
                if idx % 5 == 0 or idx == len(chunk):
                    cls._update_job_progress(job)

        # Finalize job
        job.refresh_from_db()
        job.status = ClassificationJob.Status.COMPLETED
        job.finished_at = timezone.now()
        cls._update_job_progress(job)
        job.save(update_fields=['status', 'finished_at'])

        logger.info(f"Job #{job.id} completed: {job.processed_count}/{job.total_products} processed, {job.failed_count} failed.")

        return {
            'job_id': job.id,
            'status': job.status,
            'total_products': job.total_products,
            'processed_count': job.processed_count,
            'failed_count': job.failed_count,
        }

    @classmethod
    def _process_single_product(cls, product: Product, job: ClassificationJob) -> None:
        try:
            res = classify_product(product)
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
            logger.exception(f"Classification error on SKU {product.product_number}: {exc}")
            ClassificationResult.objects.update_or_create(
                product=product,
                job=job,
                defaults={
                    'status': ClassificationResult.Status.FAILED,
                    'error_message': str(exc),
                }
            )
            job.failed_count += 1

    @classmethod
    def _update_job_progress(cls, job: ClassificationJob) -> None:
        job.processed_count = ClassificationResult.objects.filter(
            job=job,
            status__in=[ClassificationResult.Status.DONE, ClassificationResult.Status.FAILED]
        ).count()
        job.save(update_fields=['processed_count', 'failed_count'])
