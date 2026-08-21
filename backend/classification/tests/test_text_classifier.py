from django.test import TestCase
from unittest.mock import patch
from products.models import Product
from taxonomy.models import Category
from classification.engine.text_classifier import classify_text


class TextClassifierTests(TestCase):
    def setUp(self):
        Category.objects.create(
            id='gid://shopify/TaxonomyCategory/sofas',
            name='Sofas',
            full_name='Furniture > Sofas',
            level=1
        )
        self.prod = Product.objects.create(
            product_number='TEXT-TEST-1',
            product_name='Comfortable 3-Seater Fabric Sofa',
            product_description='Modern living room couch with deep cushioning.'
        )

    def test_classify_text_returns_predictions(self):
        preds, meta = classify_text(self.prod, top_k=3)
        self.assertIsInstance(preds, list)
        self.assertFalse(meta.get('is_low_info'))
