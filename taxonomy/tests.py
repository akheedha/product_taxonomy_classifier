from django.test import TestCase
from taxonomy.models import Category, Attribute, AttributeValue


class TaxonomyModelTests(TestCase):
    def setUp(self):
        # Create Category Hierarchy: Root -> Clothing -> Tops -> Shirts
        self.root = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/aa",
            name="Apparel & Accessories",
            full_name="Apparel & Accessories",
            level=0,
            parent=None
        )
        self.clothing = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/aa-1",
            name="Clothing",
            full_name="Apparel & Accessories > Clothing",
            level=1,
            parent=self.root
        )
        self.tops = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/aa-1-1",
            name="Tops",
            full_name="Apparel & Accessories > Clothing > Tops",
            level=2,
            parent=self.clothing
        )
        self.shirts = Category.objects.create(
            id="gid://shopify/TaxonomyCategory/aa-1-1-1",
            name="Shirts",
            full_name="Apparel & Accessories > Clothing > Tops > Shirts",
            level=3,
            parent=self.tops
        )

        # Create Attribute and link to categories
        self.color_attr = Attribute.objects.create(
            id="gid://shopify/TaxonomyAttribute/1",
            name="Color"
        )
        self.color_attr.categories.add(self.clothing, self.shirts)

        # Create Attribute Values
        self.color_red = AttributeValue.objects.create(
            id="gid://shopify/TaxonomyValue/101",
            attribute=self.color_attr,
            value="Red"
        )
        self.color_blue = AttributeValue.objects.create(
            id="gid://shopify/TaxonomyValue/102",
            attribute=self.color_attr,
            value="Blue"
        )

    def test_category_ancestor_chain(self):
        ancestors = self.shirts.get_ancestors(include_self=False)
        self.assertEqual(len(ancestors), 3)
        self.assertEqual([c.id for c in ancestors], [self.root.id, self.clothing.id, self.tops.id])

        ancestors_with_self = self.shirts.get_ancestors(include_self=True)
        self.assertEqual(len(ancestors_with_self), 4)
        self.assertEqual(
            [c.id for c in ancestors_with_self],
            [self.root.id, self.clothing.id, self.tops.id, self.shirts.id]
        )

        chain_names = self.shirts.get_ancestor_chain_names(include_self=True)
        self.assertEqual(
            chain_names,
            ["Apparel & Accessories", "Clothing", "Tops", "Shirts"]
        )

    def test_root_category_ancestors(self):
        self.assertEqual(self.root.get_ancestors(include_self=False), [])
        self.assertEqual(self.root.get_ancestors(include_self=True), [self.root])

    def test_attribute_category_relationship(self):
        self.assertIn(self.shirts, self.color_attr.categories.all())
        self.assertIn(self.clothing, self.color_attr.categories.all())
        self.assertEqual(self.shirts.attributes.count(), 1)
        self.assertEqual(self.shirts.attributes.first(), self.color_attr)

    def test_attribute_values(self):
        values = list(self.color_attr.values.values_list('value', flat=True))
        self.assertIn("Red", values)
        self.assertIn("Blue", values)
        self.assertEqual(str(self.color_red), "Color: Red")
