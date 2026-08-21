from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from taxonomy.models import Category, Attribute


class TaxonomyAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.cat = Category.objects.create(
            id='gid://shopify/TaxonomyCategory/fr-22',
            name='Sofas',
            full_name='Furniture > Seating > Sofas',
            level=2
        )
        self.attr = Attribute.objects.create(
            id='gid://shopify/TaxonomyAttribute/color',
            name='Color'
        )
        self.attr.categories.add(self.cat)

    def test_search_categories_api(self):
        response = self.client.get('/api/taxonomy/categories/?q=sofa')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data[0]['name'], 'Sofas')

    def test_get_category_detail_api(self):
        response = self.client.get(f'/api/taxonomy/categories/{self.cat.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Sofas')
        self.assertEqual(len(response.data['attributes']), 1)

    def test_list_attributes_for_category(self):
        response = self.client.get(f'/api/taxonomy/attributes/?category={self.cat.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], 'Color')
