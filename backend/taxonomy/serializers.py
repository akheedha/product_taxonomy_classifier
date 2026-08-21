"""
Serializers for Shopify Taxonomy models.
"""

from rest_framework import serializers
from .models import Category, Attribute, AttributeValue


class CategorySummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'full_name', 'level', 'parent']


class AttributeValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = AttributeValue
        fields = ['id', 'value']


class AttributeSerializer(serializers.ModelSerializer):
    values = AttributeValueSerializer(many=True, read_only=True)

    class Meta:
        model = Attribute
        fields = ['id', 'name', 'values']


class CategoryDetailSerializer(serializers.ModelSerializer):
    ancestor_chain = serializers.SerializerMethodField()
    attributes = AttributeSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'full_name', 'level', 'parent', 'ancestor_chain', 'attributes']

    def get_ancestor_chain(self, obj):
        return obj.get_ancestor_chain_names(include_self=True)
