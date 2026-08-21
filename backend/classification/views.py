"""
REST API views for Classification Results & Curator Reviews.
"""

from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ClassificationResult
from .serializers import (
    ClassificationResultListSerializer,
    ClassificationResultDetailSerializer,
    ClassificationReviewUpdateSerializer
)
from .services import ClassificationService


class StandardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class ClassificationResultListAPIView(generics.ListAPIView):
    """
    GET /api/results/
    Query parameters: job, needs_review, approved, min_conf, max_conf, search, category, page
    """
    pagination_class = StandardPagination
    serializer_class = ClassificationResultListSerializer

    def get_queryset(self):
        params = self.request.query_params

        job_id_raw = params.get('job')
        job_id = int(job_id_raw) if job_id_raw and job_id_raw.isdigit() else None

        needs_review_raw = params.get('needs_review')
        needs_review = None
        if needs_review_raw is not None:
            needs_review = needs_review_raw.lower() in ('true', '1', 't', 'yes')

        approved_raw = params.get('approved')
        approved = None
        if approved_raw is not None:
            approved = approved_raw.lower() in ('true', '1', 't', 'yes')

        min_conf_raw = params.get('min_conf')
        min_conf = float(min_conf_raw) if min_conf_raw else None

        max_conf_raw = params.get('max_conf')
        max_conf = float(max_conf_raw) if max_conf_raw else None

        return ClassificationService.get_filtered_results(
            job_id=job_id,
            needs_review=needs_review,
            approved=approved,
            min_confidence=min_conf,
            max_confidence=max_conf,
            search=params.get('search'),
            category=params.get('category'),
            status_filter=params.get('status'),
        )


class ClassificationResultSummaryAPIView(APIView):
    """
    GET /api/results/summary/?job=1
    Returns aggregate counts for executive KPI cards.
    """
    def get(self, request):
        job_id_raw = request.query_params.get('job')
        job_id = int(job_id_raw) if job_id_raw and job_id_raw.isdigit() else None
        metrics = ClassificationService.get_summary_metrics(job_id=job_id)
        return Response(metrics)


class ClassificationResultDetailAPIView(generics.RetrieveUpdateAPIView):
    """
    GET /api/results/{id}/
    PATCH /api/results/{id}/ (Approve / Category Override)
    """
    queryset = ClassificationResult.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PATCH', 'PUT']:
            return ClassificationReviewUpdateSerializer
        return ClassificationResultDetailSerializer
