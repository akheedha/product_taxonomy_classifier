from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Product
from processing.models import ClassificationJob
from taxonomy.models import Category
from classification.models import ClassificationResult


class ClassificationAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cat1 = Category.objects.create(
            id='gid://shopify/TaxonomyCategory/beds',
            name='Beds',
            full_name='Furniture > Beds',
            level=1
        )
        self.cat2 = Category.objects.create(
            id='gid://shopify/TaxonomyCategory/dressers',
            name='Dressers',
            full_name='Furniture > Dressers',
            level=1
        )
        self.prod = Product.objects.create(
            product_number='RESULT-SKU-1',
            product_name='King Size Platform Bed'
        )
        self.job = ClassificationJob.objects.create(total_products=1, status='completed')
        self.res = ClassificationResult.objects.create(
            product=self.prod,
            job=self.job,
            predicted_category=self.cat1,
            confidence=0.88,
            needs_manual_review=False,
            status=ClassificationResult.Status.DONE
        )

    def test_list_results_api(self):
        response = self.client.get('/api/results/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_summary_metrics_api(self):
        response = self.client.get('/api/results/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_results'], 1)
        self.assertEqual(response.data['average_confidence'], 0.88)

    def test_approve_result_api(self):
        response = self.client.patch(
            f'/api/results/{self.res.id}/',
            {'approved': True, 'reviewed_by': 'lead_curator'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.res.refresh_from_db()
        self.assertTrue(self.res.approved)
        self.assertEqual(self.res.reviewed_by, 'lead_curator')

    def test_override_category_api(self):
        response = self.client.patch(
            f'/api/results/{self.res.id}/',
            {'category_id': self.cat2.id, 'reviewed_by': 'lead_curator'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.res.refresh_from_db()
        self.assertEqual(self.res.predicted_category.id, self.cat2.id)
        self.assertEqual(self.res.confidence, 1.0)
