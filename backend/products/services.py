"""
Service layer for Product catalog domain queries and operations.
"""

from typing import Optional, List, Dict, Any
from django.db.models import Q, QuerySet
from .models import Product


class ProductService:
    @staticmethod
    def get_product_by_id(product_id: int) -> Optional[Product]:
        return Product.objects.filter(id=product_id).first()

    @staticmethod
    def get_product_by_sku(sku: str) -> Optional[Product]:
        return Product.objects.filter(product_number=sku).first()

    @staticmethod
    def filter_products(
        search: Optional[str] = None,
        category: Optional[str] = None,
        brand: Optional[str] = None
    ) -> QuerySet[Product]:
        qs = Product.objects.all()
        if search:
            s = search.strip()
            qs = qs.filter(
                Q(product_number__icontains=s) |
                Q(product_name__icontains=s) |
                Q(brand__icontains=s) |
                Q(product_category__icontains=s) |
                Q(product_sub_category__icontains=s) |
                Q(materials__icontains=s)
            )
        if category:
            qs = qs.filter(Q(product_category__icontains=category) | Q(product_sub_category__icontains=category))
        if brand:
            qs = qs.filter(brand__icontains=brand)
        return qs
