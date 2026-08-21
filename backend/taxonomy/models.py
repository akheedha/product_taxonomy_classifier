"""
================================================================================
SHOPIFY PRODUCT TAXONOMY SCHEMA MODELS
================================================================================
Purpose:
  Models the official Shopify Product Taxonomy tree (14,606 nodes), including:
    1. Category: Hierarchical tree nodes (Level 0 Root -> Level 5 Leaves).
    2. Attribute: Taxonomy attributes (Color, Material, Pattern, Furniture Style).
    3. AttributeValue: Canonical allowed values for attributes (e.g. 'Teak', 'Navy Blue').
"""

from django.db import models


class Category(models.Model):
    """
    Shopify Product Taxonomy Category model.
    Represents hierarchical product categories (e.g. Apparel & Accessories > Clothing > Shirts).
    """
    id = models.CharField(
        max_length=255,
        primary_key=True,
        help_text="Shopify taxonomy GID (e.g. gid://shopify/TaxonomyCategory/aa-1) or identifier"
    )
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Category local name (e.g. Shirts)"
    )
    full_name = models.CharField(
        max_length=500,
        db_index=True,
        help_text="Full category breadcrumb path (e.g. Apparel & Accessories > Clothing > Tops > Shirts)"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        db_index=True,
        help_text="Parent category in the taxonomy tree"
    )
    level = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Depth level in taxonomy hierarchy (0 = Root)"
    )

    class Meta:
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['level', 'name']

    def __str__(self):
        return self.full_name or self.name or self.id

    def get_ancestors(self, include_self: bool = False) -> list['Category']:
        """
        Returns a list of ancestor Category instances ordered from root down to parent
        (or including self if include_self=True).
        Cycle-safe implementation.
        """
        ancestors = []
        current = self if include_self else self.parent
        visited = set()
        while current is not None and current.pk not in visited:
            visited.add(current.pk)
            ancestors.append(current)
            current = current.parent
        ancestors.reverse()
        return ancestors

    def get_ancestor_chain_names(self, include_self: bool = True) -> list[str]:
        """
        Returns list of category names from root down to self/parent.
        """
        return [cat.name for cat in self.get_ancestors(include_self=include_self)]


class Attribute(models.Model):
    """
    Shopify Taxonomy Attribute (e.g. Color, Size, Material, Pattern).
    An attribute can be associated with multiple categories.
    """
    id = models.CharField(
        max_length=255,
        primary_key=True,
        help_text="Shopify taxonomy attribute GID (e.g. gid://shopify/TaxonomyAttribute/1) or identifier"
    )
    name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Attribute name (e.g. Color, Sleeve Length)"
    )
    categories = models.ManyToManyField(
        Category,
        related_name='attributes',
        blank=True,
        help_text="Categories to which this attribute applies"
    )

    class Meta:
        verbose_name = 'Attribute'
        verbose_name_plural = 'Attributes'
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.id})"


class AttributeValue(models.Model):
    """
    Allowed/predefined value for a given taxonomy attribute.
    (e.g. Attribute: Color -> Value: 'Red', 'Navy Blue').
    """
    id = models.CharField(
        max_length=255,
        primary_key=True,
        help_text="Shopify taxonomy attribute value GID (e.g. gid://shopify/TaxonomyValue/1) or identifier"
    )
    attribute = models.ForeignKey(
        Attribute,
        on_delete=models.CASCADE,
        related_name='values',
        help_text="The attribute this value belongs to"
    )
    value = models.CharField(
        max_length=255,
        db_index=True,
        help_text="The value string (e.g. Red, XL, Cotton)"
    )

    class Meta:
        verbose_name = 'Attribute Value'
        verbose_name_plural = 'Attribute Values'
        ordering = ['attribute', 'value']

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"
