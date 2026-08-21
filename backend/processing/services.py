"""
Processing Job Management Service layer.
"""

from typing import Dict, Any, Optional
from products.models import Product
from .models import ClassificationJob
from .tasks import process_classification_job
from .batch_processor import BatchProcessor


class ProcessingService:
    @staticmethod
    def create_and_dispatch_job(limit: Optional[int] = None, sync: bool = False) -> ClassificationJob:
        total = Product.objects.count() if limit is None else min(limit, Product.objects.count())
        job = ClassificationJob.objects.create(
            total_products=total,
            status=ClassificationJob.Status.PENDING
        )

        if sync:
            BatchProcessor.process_job(job.id)
            job.refresh_from_db()
        else:
            try:
                process_classification_job.delay(job.id)
            except Exception:
                # Fallback to sync if Celery/Redis broker is not reachable
                BatchProcessor.process_job(job.id)
                job.refresh_from_db()

        return job

    @staticmethod
    def resume_job(job_id: int, sync: bool = False) -> Optional[ClassificationJob]:
        job = ClassificationJob.objects.filter(id=job_id).first()
        if not job:
            return None

        if sync:
            BatchProcessor.process_job(job.id)
            job.refresh_from_db()
        else:
            try:
                process_classification_job.delay(job.id)
            except Exception:
                BatchProcessor.process_job(job.id)
                job.refresh_from_db()

        return job
