from django.test import TestCase
from products.models import Product
from taxonomy.models import Category
from processing.models import ClassificationJob
from processing.batch_processor import BatchProcessor
from classification.models import ClassificationResult


class BatchProcessorTests(TestCase):
    def setUp(self):
        Category.objects.create(
            id='gid://shopify/TaxonomyCategory/desks',
            name='Desks',
            full_name='Furniture > Tables > Desks',
            level=2
        )
        self.p1 = Product.objects.create(
            product_number='BATCH-SKU-1',
            product_name='Executive Walnut Office Desk'
        )
        self.p2 = Product.objects.create(
            product_number='BATCH-SKU-2',
            product_name='L-Shaped Corner Computer Desk'
        )

    def test_process_job_executes_batch(self):
        job = ClassificationJob.objects.create(total_products=2)
        res = BatchProcessor.process_job(job.id, chunk_size=1)

        self.assertEqual(res['status'], ClassificationJob.Status.COMPLETED)
        self.assertEqual(res['processed_count'], 2)
        self.assertEqual(res['failed_count'], 0)

        results = ClassificationResult.objects.filter(job=job)
        self.assertEqual(results.count(), 2)
        self.assertTrue(all(r.status == ClassificationResult.Status.DONE for r in results))
