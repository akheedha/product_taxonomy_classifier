"""
Taxonomy Domain Service layer.
"""

from typing import Optional, List
from django.db.models import Q, QuerySet
from .models import Category, Attribute


class TaxonomyService:
    @staticmethod
    def search_categories(
        query: Optional[str] = None,
        level: Optional[int] = None,
        parent_id: Optional[str] = None,
        limit: int = 50
    ) -> QuerySet[Category]:
        qs = Category.objects.all()
        if query:
            q_str = query.strip()
            qs = qs.filter(Q(name__icontains=q_str) | Q(full_name__icontains=q_str) | Q(id__icontains=q_str))
        if level is not None:
            qs = qs.filter(level=level)
        if parent_id:
            qs = qs.filter(parent_id=parent_id)
        return qs[:limit]

    @staticmethod
    def get_category_by_id(category_id: str) -> Optional[Category]:
        return Category.objects.filter(id=category_id).first()

    @staticmethod
    def get_attributes_for_category(category_id: str) -> QuerySet[Attribute]:
        category = Category.objects.filter(id=category_id).first()
        if not category:
            return Attribute.objects.none()

        direct_attrs = Attribute.objects.filter(categories__id=category_id).prefetch_related('values')
        if direct_attrs.exists():
            return direct_attrs

        ancestor_ids = [a.id for a in category.get_ancestors(include_self=False)]
        if ancestor_ids:
            return Attribute.objects.filter(categories__id__in=ancestor_ids).distinct().prefetch_related('values')

        return Attribute.objects.none()
