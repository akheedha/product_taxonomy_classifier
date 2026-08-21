from django.test import TestCase
from products.models import Product


class ProductModelTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(
            product_number='TEST-SKU-001',
            product_name='Modern Velvet Accent Chair',
            brand='Nordic Home',
            product_category='Furniture',
            product_sub_category='Chairs',
            materials='Solid Oak Wood, Velvet Fabric',
            images=['https://images.example.com/chair1.jpg', 'https://images.example.com/chair2.jpg']
        )

    def test_product_str(self):
        self.assertEqual(str(self.product), 'TEST-SKU-001 - Modern Velvet Accent Chair')

    def test_primary_image_property(self):
        self.assertEqual(self.product.primary_image, 'https://images.example.com/chair1.jpg')

    def test_image_count_property(self):
        self.assertEqual(self.product.image_count, 2)

    def test_primary_image_empty(self):
        p_no_img = Product.objects.create(product_number='TEST-SKU-EMPTY', images=[])
        self.assertIsNone(p_no_img.primary_image)
        self.assertEqual(p_no_img.image_count, 0)
