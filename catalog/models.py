"""
================================================================================
CATALOG PRODUCT MODELS
================================================================================
Purpose:
  Defines the Product data model representing raw catalog SKUs imported from
  spreadsheets (.xlsx, .xls, .csv). Stores all attributes, dimensions, pricing,
  marketing copy, and aggregated media arrays (up to 20 images per product).
"""

from django.db import models


class Product(models.Model):
    """
    Catalog Product model representing ingested product catalog records.
    Stores detailed product attributes, pricing, dimensions, and media.
    """
    product_number = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Unique product identifier / SKU"
    )
    model_number = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Product model number"
    )
    product_category = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Raw source product category"
    )
    product_sub_category = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Raw source product sub-category"
    )
    collection_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Collection or line name"
    )
    color_collection = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Color collection family"
    )
    product_color = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Specific product color / finish"
    )
    product_name = models.CharField(
        max_length=500,
        null=True,
        blank=True,
        db_index=True,
        help_text="Product title / name"
    )
    brand = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        db_index=True,
        help_text="Brand, vendor, or manufacturer name"
    )
    product_description = models.TextField(
        null=True,
        blank=True,
        help_text="Detailed marketing description"
    )
    bullets = models.TextField(
        null=True,
        blank=True,
        help_text="Feature bullet points"
    )
    set_includes = models.TextField(
        null=True,
        blank=True,
        help_text="Set inclusions / contents description"
    )
    product_weight = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Product weight (e.g. '105')"
    )
    materials = models.TextField(
        null=True,
        blank=True,
        help_text="Materials & construction details"
    )
    product_dimensions = models.TextField(
        null=True,
        blank=True,
        help_text="Product dimensions & measurements"
    )
    assembly_required = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Assembly required indicator (Y/N)"
    )
    is_set = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Is a set indicator (Y/N)"
    )
    stackable = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Stackable indicator (Y/N)"
    )
    country_of_origin = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Country of origin / manufacturing"
    )
    item_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Wholesale item cost"
    )
    map_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum Advertised Price (MAP)"
    )
    msrp = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Manufacturer Suggested Retail Price (MSRP)"
    )
    images = models.JSONField(
        default=list,
        blank=True,
        help_text="List of up to 20 image URLs"
    )
    shipping_method = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Shipping method / freight type"
    )
    total_box_count = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Total number of shipping boxes"
    )
    pallet_count = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        help_text="Pallet count"
    )
    shipping_weight = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Total shipping weight"
    )
    total_cbm = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Total cubic meters (CBM)"
    )
    package_dimensions = models.TextField(
        null=True,
        blank=True,
        help_text="Package / carton dimensions"
    )
    product_url = models.CharField(
        max_length=1000,
        null=True,
        blank=True,
        help_text="Source product URL"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['product_number']

    def __str__(self):
        return f"{self.product_number} - {self.product_name or 'Untitled Product'}"

    @property
    def primary_image(self) -> str | None:
        """Returns the first image URL if available."""
        if self.images and isinstance(self.images, list) and len(self.images) > 0:
            return self.images[0]
        return None

    @property
    def image_count(self) -> int:
        """Returns count of image URLs."""
        if self.images and isinstance(self.images, list):
            return len(self.images)
        return 0
