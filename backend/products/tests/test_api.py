from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Product


class ProductAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.p1 = Product.objects.create(
            product_number='SKU-API-1',
            product_name='Outdoor Dining Table',
            brand='PatioCraft'
        )

    def test_list_products_api(self):
        response = self.client.get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['product_number'], 'SKU-API-1')

    def test_detail_product_api(self):
        response = self.client.get(f'/api/products/{self.p1.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['product_name'], 'Outdoor Dining Table')
