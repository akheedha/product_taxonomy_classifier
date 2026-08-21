from django.test import TestCase
from products.models import Product
from products.services import ProductService


class ProductServiceTests(TestCase):
    def setUp(self):
        Product.objects.create(
            product_number='SKU-SOFA-1',
            product_name='Scandinavian 3-Seater Sofa',
            brand='Nordic Living',
            product_category='Furniture',
            product_sub_category='Sofas'
        )
        Product.objects.create(
            product_number='SKU-LAMP-1',
            product_name='Modern Brass Floor Lamp',
            brand='Lumina',
            product_category='Lighting',
            product_sub_category='Lamps'
        )

    def test_get_product_by_sku(self):
        prod = ProductService.get_product_by_sku('SKU-SOFA-1')
        self.assertIsNotNone(prod)
        self.assertEqual(prod.brand, 'Nordic Living')

    def test_filter_products_by_search(self):
        qs = ProductService.filter_products(search='Scandinavian')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().product_number, 'SKU-SOFA-1')

    def test_filter_products_by_category(self):
        qs = ProductService.filter_products(category='Lighting')
        self.assertEqual(qs.count(), 1)
        self.assertEqual(qs.first().product_number, 'SKU-LAMP-1')
