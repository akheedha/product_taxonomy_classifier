from django.test import TestCase
from taxonomy.models import Category, Attribute, AttributeValue


class TaxonomyModelTests(TestCase):
    def setUp(self):
        self.root = Category.objects.create(
            id='gid://shopify/TaxonomyCategory/root',
            name='Furniture',
            full_name='Furniture',
            level=0
        )
        self.child = Category.objects.create(
            id='gid://shopify/TaxonomyCategory/seating',
            name='Seating',
            full_name='Furniture > Seating',
            parent=self.root,
            level=1
        )
        self.leaf = Category.objects.create(
            id='gid://shopify/TaxonomyCategory/chairs',
            name='Chairs',
            full_name='Furniture > Seating > Chairs',
            parent=self.child,
            level=2
        )

    def test_category_ancestor_chain(self):
        chain = self.leaf.get_ancestor_chain_names(include_self=True)
        self.assertEqual(chain, ['Furniture', 'Seating', 'Chairs'])

    def test_category_ancestors_exclude_self(self):
        ancestors = self.leaf.get_ancestors(include_self=False)
        self.assertEqual(len(ancestors), 2)
        self.assertEqual(ancestors[0].name, 'Furniture')
        self.assertEqual(ancestors[1].name, 'Seating')

    def test_attributes_association(self):
        attr = Attribute.objects.create(id='gid://shopify/TaxonomyAttribute/1', name='Material')
        attr.categories.add(self.leaf)
        val = AttributeValue.objects.create(id='gid://shopify/TaxonomyValue/1', attribute=attr, value='Velvet')

        self.assertEqual(self.leaf.attributes.count(), 1)
        self.assertEqual(attr.values.count(), 1)
        self.assertEqual(str(val), 'Material: Velvet')
