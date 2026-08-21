"""
REST API views for Shopify Taxonomy exploration and search.
"""

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Category, Attribute
from .serializers import CategorySummarySerializer, CategoryDetailSerializer, AttributeSerializer
from .services import TaxonomyService


class CategoryListAPIView(generics.ListAPIView):
    """
    GET /api/taxonomy/categories/?q=sofa&level=2&parent=...
    """
    serializer_class = CategorySummarySerializer

    def get_queryset(self):
        query = self.request.query_params.get('q')
        level_str = self.request.query_params.get('level')
        level = int(level_str) if level_str and level_str.isdigit() else None
        parent_id = self.request.query_params.get('parent')
        return TaxonomyService.search_categories(query=query, level=level, parent_id=parent_id, limit=100)


class CategoryDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/taxonomy/categories/{id}/
    """
    queryset = Category.objects.all()
    serializer_class = CategoryDetailSerializer


class AttributeListAPIView(generics.ListAPIView):
    """
    GET /api/taxonomy/attributes/?category=gid://shopify/...
    """
    serializer_class = AttributeSerializer

    def get_queryset(self):
        category_id = self.request.query_params.get('category')
        if category_id:
            return TaxonomyService.get_attributes_for_category(category_id)
        return Attribute.objects.all().prefetch_related('values')[:50]
