"""
Serializers for Product entity.
"""

from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """Full Product model serializer."""
    primary_image = serializers.ReadOnlyField()
    image_count = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = '__all__'


class ProductSummarySerializer(serializers.ModelSerializer):
    """Compact serializer for table rows and summaries."""
    primary_image = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id',
            'product_number',
            'product_name',
            'brand',
            'product_category',
            'product_sub_category',
            'materials',
            'product_color',
            'product_description',
            'bullets',
            'product_dimensions',
            'primary_image',
            'images',
        ]
