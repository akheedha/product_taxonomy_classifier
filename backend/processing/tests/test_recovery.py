from django.test import TestCase
from products.models import Product
from taxonomy.models import Category
from processing.models import ClassificationJob
from processing.batch_processor import BatchProcessor
from classification.models import ClassificationResult


class RecoveryAndResumabilityTests(TestCase):
    def setUp(self):
        Category.objects.create(
            id='gid://shopify/TaxonomyCategory/rugs',
            name='Rugs',
            full_name='Home & Garden > Linens & Bedding > Rugs',
            level=2
        )
        self.p1 = Product.objects.create(product_number='RESUME-1', product_name='Persian Wool Rug')
        self.p2 = Product.objects.create(product_number='RESUME-2', product_name='Jute Area Rug')
        self.p3 = Product.objects.create(product_number='RESUME-3', product_name='Boho Runner Rug')

    def test_resume_skips_already_done_products(self):
        job = ClassificationJob.objects.create(total_products=3)
        # Pre-mark p1 as DONE
        ClassificationResult.objects.create(
            product=self.p1,
            job=job,
            status=ClassificationResult.Status.DONE,
            confidence=0.92
        )

        # Resume job
        res = BatchProcessor.process_job(job.id, chunk_size=2)
        self.assertEqual(res['status'], ClassificationJob.Status.COMPLETED)
        self.assertEqual(res['processed_count'], 3)

        # Total completed records should be 3
        self.assertEqual(ClassificationResult.objects.filter(job=job, status=ClassificationResult.Status.DONE).count(), 3)
