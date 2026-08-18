import os
import tempfile
from decimal import Decimal
import pandas as pd
from django.core.management import call_command
from django.test import TestCase
from catalog.models import Product


class ProductModelTests(TestCase):
    def test_create_product(self):
        product = Product.objects.create(
            product_number="TEST-SKU-100",
            model_number="MOD-100",
            product_name="Modern Velvet Armchair",
            product_category="Living Room",
            product_sub_category="Chairs",
            product_description="Comfortable velvet armchair for modern spaces.",
            item_cost=Decimal("150.00"),
            map_price=Decimal("299.99"),
            msrp=Decimal("499.99"),
            images=[
                "https://example.com/images/chair1.jpg",
                "https://example.com/images/chair2.jpg"
            ]
        )

        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(product.product_number, "TEST-SKU-100")
        self.assertEqual(product.primary_image, "https://example.com/images/chair1.jpg")
        self.assertEqual(product.image_count, 2)
        self.assertEqual(str(product), "TEST-SKU-100 - Modern Velvet Armchair")


class ImportProductsCommandTests(TestCase):
    def test_import_products_from_csv(self):
        # Create a sample DataFrame with diverse data quality conditions
        data = {
            'Product Number': ['SKU-001', 'SKU-002', None, '   ', 'SKU-003'],
            'Model Number': ['MOD-1', 'MOD-2', 'MOD-3', 'MOD-4', 'MOD-5'],
            'Product Category': ['Living Room', None, 'Dining', 'Bedroom', 'Office'],
            'Product Sub Category': ['Sofas', None, 'Tables', 'Beds', 'Desks'],
            'Product Name': ['Leather Sofa', 'Armchair', 'Oak Table', 'King Bed', 'Standing Desk'],
            'Product Description': ['Luxury leather sofa.', None, 'Solid oak.', 'Wooden bed.', 'Adjustable desk.'],
            'Item Cost': [400.0, 150.5, None, 300.0, 250.0],
            'MAP': [699.0, None, 450.0, 550.0, 399.0],
            'MSRP': [999.0, 299.0, 600.0, 799.0, 499.0],
            'Image 1': ['https://example.com/img1.jpg', 'https://example.com/img2.jpg', None, None, None],
            'Image 2': ['https://example.com/img1_alt.jpg', None, None, None, None],
            'Image 3': ['Freight', None, None, None, None],  # Non-URL artifact to test filter
        }
        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
            tmp_path = tmp.name
            df.to_excel(tmp_path, index=False)

        try:
            # Run management command
            call_command('import_products', tmp_path)

            # Verification: Rows with None or blank product numbers should be skipped (2 skipped)
            self.assertEqual(Product.objects.count(), 3)

            p1 = Product.objects.get(product_number='SKU-001')
            self.assertEqual(p1.product_name, 'Leather Sofa')
            self.assertEqual(p1.product_category, 'Living Room')
            self.assertEqual(p1.images, ['https://example.com/img1.jpg', 'https://example.com/img1_alt.jpg'])
            self.assertEqual(p1.image_count, 2)

            p2 = Product.objects.get(product_number='SKU-002')
            self.assertIsNone(p2.product_description)
            self.assertIsNone(p2.product_category)
            self.assertEqual(p2.image_count, 1)

            p3 = Product.objects.get(product_number='SKU-003')
            self.assertEqual(p3.image_count, 0)
            self.assertIsNone(p3.primary_image)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
