from django.test import TestCase
from unittest.mock import patch
from processing.models import ClassificationJob
from processing.tasks import process_classification_job


class TaskExecutionTests(TestCase):
    @patch('processing.batch_processor.BatchProcessor.process_job')
    def test_celery_task_delegates_to_batch_processor(self, mock_process):
        mock_process.return_value = {'status': 'completed', 'processed_count': 10}
        job = ClassificationJob.objects.create(total_products=10)

        result = process_classification_job(job.id)
        mock_process.assert_called_once_with(job_id=job.id)
        self.assertEqual(result['status'], 'completed')
