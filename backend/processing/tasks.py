"""
Celery asynchronous background tasks for batch processing.
"""

import logging
from typing import Dict, Any
from celery import shared_task
from .batch_processor import BatchProcessor

logger = logging.getLogger(__name__)


@shared_task(bind=True, name='processing.tasks.process_classification_job')
def process_classification_job(self, job_id: int) -> Dict[str, Any]:
    """
    Celery worker task delegating batch execution to BatchProcessor.
    """
    logger.info(f"Celery worker received job #{job_id}")
    return BatchProcessor.process_job(job_id=job_id)


# Legacy task alias for backward compatibility
@shared_task(bind=True, name='classification.tasks.process_classification_job')
def legacy_process_classification_job(self, job_id: int) -> Dict[str, Any]:
    return BatchProcessor.process_job(job_id=job_id)
