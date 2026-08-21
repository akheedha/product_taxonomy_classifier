from django.test import TestCase
from products.models import Product
from taxonomy.models import Category, Attribute, AttributeValue
from classification.engine.attribute_extractor import extract_attributes


class AttributeExtractorTests(TestCase):
    def setUp(self):
        self.cat = Category.objects.create(
            id='gid://shopify/TaxonomyCategory/chairs',
            name='Chairs',
            full_name='Furniture > Chairs',
            level=1
        )
        self.attr_color = Attribute.objects.create(
            id='gid://shopify/TaxonomyAttribute/color',
            name='Color'
        )
        self.attr_color.categories.add(self.cat)
        AttributeValue.objects.create(
            id='gid://shopify/TaxonomyValue/navy',
            attribute=self.attr_color,
            value='Navy Blue'
        )

        self.prod = Product.objects.create(
            product_number='ATTR-TEST-1',
            product_name='Navy Blue Velvet Chair',
            product_color='Navy Blue',
            materials='Velvet, Wood'
        )

    def test_extract_attributes_from_product(self):
        extracted = extract_attributes(self.prod, self.cat)
        self.assertIn('Color', extracted)
        self.assertEqual(extracted['Color']['value'], 'Navy Blue')
        self.assertGreater(extracted['Color']['confidence'], 0.8)
