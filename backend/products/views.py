"""
REST API views for Product catalog.
"""

from rest_framework import generics
from rest_framework.pagination import PageNumberPagination
from .models import Product
from .serializers import ProductSerializer, ProductSummarySerializer
from .services import ProductService


class StandardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class ProductListAPIView(generics.ListAPIView):
    """
    GET /api/products/
    Query parameters: search, category, brand, page
    """
    pagination_class = StandardPagination
    serializer_class = ProductSummarySerializer

    def get_queryset(self):
        return ProductService.filter_products(
            search=self.request.query_params.get('search'),
            category=self.request.query_params.get('category'),
            brand=self.request.query_params.get('brand'),
        )


class ProductDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/products/{id}/
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
