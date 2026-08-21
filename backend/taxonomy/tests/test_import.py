from django.test import TestCase
from taxonomy.models import Category
from taxonomy.services import TaxonomyService


class TaxonomyServiceTests(TestCase):
    def setUp(self):
        Category.objects.create(
            id='gid://shopify/TaxonomyCategory/t-1',
            name='Dining Tables',
            full_name='Furniture > Tables > Dining Tables',
            level=2
        )

    def test_search_categories_service(self):
        results = TaxonomyService.search_categories('Dining')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, 'Dining Tables')

    def test_get_category_by_id_service(self):
        cat = TaxonomyService.get_category_by_id('gid://shopify/TaxonomyCategory/t-1')
        self.assertIsNotNone(cat)
        self.assertEqual(cat.full_name, 'Furniture > Tables > Dining Tables')
