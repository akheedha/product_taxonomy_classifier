"""
Classification Domain Service layer.
"""

from typing import Dict, Any, Optional
from django.db.models import Q, QuerySet, Avg, Count
from .models import ClassificationResult
from .engine.fusion import classify_product


class ClassificationService:
    @staticmethod
    def get_filtered_results(
        job_id: Optional[int] = None,
        needs_review: Optional[bool] = None,
        approved: Optional[bool] = None,
        min_confidence: Optional[float] = None,
        max_confidence: Optional[float] = None,
        search: Optional[str] = None,
        category: Optional[str] = None,
        status_filter: Optional[str] = None
    ) -> QuerySet[ClassificationResult]:
        qs = ClassificationResult.objects.select_related('product', 'predicted_category', 'job')

        if job_id is not None:
            qs = qs.filter(job_id=job_id)

        if needs_review is not None:
            qs = qs.filter(needs_manual_review=needs_review)

        if approved is not None:
            qs = qs.filter(approved=approved)

        if min_confidence is not None:
            qs = qs.filter(confidence__gte=min_confidence)

        if max_confidence is not None:
            qs = qs.filter(confidence__lte=max_confidence)

        if status_filter:
            qs = qs.filter(status=status_filter)

        if search:
            s = search.strip()
            qs = qs.filter(
                Q(product__product_number__icontains=s) |
                Q(product__product_name__icontains=s) |
                Q(product__brand__icontains=s) |
                Q(predicted_category__name__icontains=s) |
                Q(predicted_category__full_name__icontains=s)
            )

        if category:
            qs = qs.filter(
                Q(predicted_category__name__icontains=category) |
                Q(predicted_category__full_name__icontains=category)
            )

        return qs

    @staticmethod
    def get_summary_metrics(job_id: Optional[int] = None) -> Dict[str, Any]:
        qs = ClassificationResult.objects.all()
        if job_id is not None:
            qs = qs.filter(job_id=job_id)

        total = qs.count()
        if total == 0:
            return {
                'total_results': 0,
                'approved_count': 0,
                'needs_review_count': 0,
                'failed_count': 0,
                'average_confidence': 0.0,
                'approval_rate_percent': 0.0,
                'review_rate_percent': 0.0,
            }

        counts = qs.aggregate(
            approved=Count('id', filter=Q(approved=True)),
            needs_review=Count('id', filter=Q(needs_manual_review=True)),
            failed=Count('id', filter=Q(status=ClassificationResult.Status.FAILED)),
            avg_conf=Avg('confidence')
        )

        approved = counts.get('approved') or 0
        needs_review = counts.get('needs_review') or 0
        failed = counts.get('failed') or 0
        avg_conf = round(counts.get('avg_conf') or 0.0, 3)

        return {
            'total_results': total,
            'approved_count': approved,
            'needs_review_count': needs_review,
            'failed_count': failed,
            'average_confidence': avg_conf,
            'approval_rate_percent': round((approved / total) * 100, 1),
            'review_rate_percent': round((needs_review / total) * 100, 1),
        }

    @staticmethod
    def run_prediction_for_product(product: Any) -> Dict[str, Any]:
        return classify_product(product)
