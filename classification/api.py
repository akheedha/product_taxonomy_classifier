"""
================================================================================
CLASSIFICATION & CURATOR REVIEW REST API ENDPOINTS
================================================================================
Purpose:
  Provides the RESTful API contract between the Django backend and the React+Vite
  curator review dashboard.

Endpoints:
  1. POST /api/jobs/               -> Create and queue a new classification job.
  2. GET  /api/jobs/               -> List classification jobs and status.
  3. GET  /api/jobs/{id}/          -> Retrieve live progress and timing of a specific job.
  4. GET  /api/results/            -> Paginated, filtered list of classified products.
  5. GET  /api/results/summary/    -> Aggregate KPI counts for summary metric cards.
  6. GET  /api/results/{id}/       -> Detailed view of an individual classification result.
  7. PATCH /api/results/{id}/      -> In-place curator actions (Approve, Category Override).
"""

import logging
from typing import Any, Dict
from django.db.models import Q
from django.db.models import Count
from rest_framework import generics, serializers, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Product
from taxonomy.models import Category
from .models import ClassificationJob, ClassificationResult
from .tasks import process_classification_job

logger = logging.getLogger(__name__)


# ==============================================================================
# PAGINATION
# ==============================================================================

class ClassificationPagination(PageNumberPagination):
    """
    Standard pagination for large product catalog tables.
    Default page size: 50 products.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


# ==============================================================================
# SERIALIZERS (DATA TRANSFER OBJECTS)
# ==============================================================================

class CategorySummarySerializer(serializers.ModelSerializer):
    """Serializes compact category hierarchy for table display."""
    class Meta:
        model = Category
        fields = ['id', 'name', 'full_name', 'level']


class ProductSummarySerializer(serializers.ModelSerializer):
    """Serializes essential product attributes and images for table rows."""
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
            'primary_image',
            'images',
        ]


class ClassificationJobSerializer(serializers.ModelSerializer):
    """
    Serializes ClassificationJob instances.
    Dynamically computes real-time processed_count and progress_percentage
    directly from completed result records for instant UI progress bar updates.
    """
    progress_percentage = serializers.SerializerMethodField()
    processed_count = serializers.SerializerMethodField()
    duration_seconds = serializers.ReadOnlyField()

    class Meta:
        model = ClassificationJob
        fields = [
            'id',
            'status',
            'progress_percentage',
            'total_products',
            'processed_count',
            'failed_count',
            'created_at',
            'started_at',
            'finished_at',
            'duration_seconds',
        ]

    def get_processed_count(self, obj) -> int:
        """Calculates live completed product count during Celery execution."""
        if obj.status == ClassificationJob.Status.COMPLETED:
            return obj.processed_count or obj.total_products
        live_count = obj.results.filter(
            status__in=[ClassificationResult.Status.DONE, ClassificationResult.Status.FAILED]
        ).count()
        return max(obj.processed_count, live_count)

    def get_progress_percentage(self, obj) -> float:
        """Calculates live completion percentage (0.0% to 100.0%)."""
        processed = self.get_processed_count(obj)
        if obj.total_products > 0:
            return round((processed / obj.total_products) * 100, 1)
        return 0.0


class JobCreateSerializer(serializers.Serializer):
    """Validates payload when launching a new classification job."""
    limit = serializers.IntegerField(required=False, min_value=1, default=None, allow_null=True)
    all = serializers.BooleanField(required=False, default=False)
    sync = serializers.BooleanField(required=False, default=False)


class ClassificationResultListSerializer(serializers.ModelSerializer):
    """Serializes result items for the paginated table grid."""
    product = ProductSummarySerializer(read_only=True)
    predicted_category = CategorySummarySerializer(read_only=True)

    class Meta:
        model = ClassificationResult
        fields = [
            'id',
            'job',
            'product',
            'predicted_category',
            'confidence',
            'alternative_categories',
            'extracted_attributes',
            'needs_manual_review',
            'status',
            'error_message',
            'approved',
            'reviewed_by',
            'updated_at',
        ]


class ClassificationResultDetailSerializer(serializers.ModelSerializer):
    """Full detail view for inspecting single result alternatives and attributes."""
    product = ProductSummarySerializer(read_only=True)
    predicted_category = CategorySummarySerializer(read_only=True)

    class Meta:
        model = ClassificationResult
        fields = [
            'id',
            'job',
            'product',
            'predicted_category',
            'confidence',
            'alternative_categories',
            'extracted_attributes',
            'needs_manual_review',
            'status',
            'error_message',
            'reviewed_by',
            'approved',
            'created_at',
            'updated_at',
        ]


class ClassificationResultUpdateSerializer(serializers.Serializer):
    """Validates in-place curator edits: Approval, Category Override, and Reviewer Name."""
    approved = serializers.BooleanField(required=False)
    override_category_id = serializers.CharField(required=False, allow_blank=True)
    reviewed_by = serializers.CharField(required=False, max_length=150, allow_blank=True)

    def validate_override_category_id(self, value):
        if value:
            if not Category.objects.filter(id=value).exists():
                raise serializers.ValidationError(f"Category with ID '{value}' does not exist in Shopify taxonomy.")
        return value


# ==============================================================================
# API VIEWS
# ==============================================================================

class JobListCreateAPIView(APIView):
    """
    POST /api/jobs/ - Start a new classification job.
    GET  /api/jobs/ - List all historical classification runs.
    """
    def get(self, request):
        jobs = ClassificationJob.objects.all().order_by('-created_at')
        serializer = ClassificationJobSerializer(jobs, many=True)
        return Response(serializer.data)

    def post(self, request):
        input_serializer = JobCreateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)
        limit = input_serializer.validated_data.get('limit')
        force_all = input_serializer.validated_data.get('all', False)
        run_sync = input_serializer.validated_data.get('sync', False)

        # 1. Filter target unclassified products
        if force_all:
            queryset = Product.objects.all().order_by('id')
        else:
            done_product_ids = ClassificationResult.objects.filter(
                status=ClassificationResult.Status.DONE
            ).values_list('product_id', flat=True)
            queryset = Product.objects.exclude(id__in=done_product_ids).order_by('id')

        if limit:
            products = list(queryset[:limit])
        else:
            products = list(queryset)

        if not products:
            return Response(
                {"detail": "No unclassified products available in catalog."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Create Job Record
        job = ClassificationJob.objects.create(
            status=ClassificationJob.Status.PENDING,
            total_products=len(products),
            processed_count=0,
            failed_count=0
        )

        # 3. Pre-seed ClassificationResult records with PENDING status
        result_stubs = [
            ClassificationResult(
                product=product,
                job=job,
                status=ClassificationResult.Status.PENDING
            )
            for product in products
        ]
        ClassificationResult.objects.bulk_create(result_stubs, batch_size=500)

        # 4. Dispatch Asynchronous Celery Task (or fallback to synchronous execution)
        if run_sync:
            process_classification_job(job.id)
            job.refresh_from_db()
        else:
            try:
                process_classification_job.delay(job.id)
            except Exception as e:
                logger.warning(f"Failed to dispatch to Celery ({e}). Executing synchronously...")
                process_classification_job(job.id)
                job.refresh_from_db()

        return Response(
            ClassificationJobSerializer(job).data,
            status=status.HTTP_201_CREATED
        )


class JobDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/jobs/{id}/ - Retrieves live job execution status and percentage.
    """
    queryset = ClassificationJob.objects.all()
    serializer_class = ClassificationJobSerializer
    lookup_field = 'pk'


class ResultListAPIView(generics.ListAPIView):
    """
    GET /api/results/ - Paginated list of classification results with rich query filters.
    Query Filters:
      - job: int (Filter by specific classification run)
      - needs_review: bool (Show only items requiring curator attention)
      - min_confidence / max_confidence: float (Confidence slider range)
      - category / search: str (Search across SKU, product title, category, and materials)
      - approved: bool (Filter by approved / pending approval)
    """
    serializer_class = ClassificationResultListSerializer
    pagination_class = ClassificationPagination

    def get_queryset(self):
        queryset = ClassificationResult.objects.select_related(
            'product', 'predicted_category', 'job'
        ).order_by('-updated_at')

        params = self.request.query_params

        # Filter by job ID
        job_id = params.get('job')
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        # Filter by manual review flag
        needs_review = params.get('needs_review') or params.get('needs_manual_review')
        if needs_review is not None:
            if needs_review.lower() in ('true', '1', 'yes'):
                queryset = queryset.filter(needs_manual_review=True)
            elif needs_review.lower() in ('false', '0', 'no'):
                queryset = queryset.filter(needs_manual_review=False)

        # Filter by confidence range
        min_conf = params.get('min_confidence')
        if min_conf:
            try:
                queryset = queryset.filter(confidence__gte=float(min_conf))
            except ValueError:
                pass

        max_conf = params.get('max_confidence')
        if max_conf:
            try:
                queryset = queryset.filter(confidence__lte=float(max_conf))
            except ValueError:
                pass

        # Text search across product attributes and predicted categories
        search = params.get('category') or params.get('search')
        if search:
            queryset = queryset.filter(
                Q(predicted_category_id=search) |
                Q(predicted_category__name__icontains=search) |
                Q(predicted_category__full_name__icontains=search) |
                Q(product__product_number__icontains=search) |
                Q(product__product_name__icontains=search) |
                Q(product__product_category__icontains=search) |
                Q(product__product_sub_category__icontains=search) |
                Q(product__materials__icontains=search)
            )

        # Filter by approval status
        approved = params.get('approved')
        if approved is not None:
            if approved.lower() in ('true', '1', 'yes'):
                queryset = queryset.filter(approved=True)
            elif approved.lower() in ('false', '0', 'no'):
                queryset = queryset.filter(approved=False)

        # Filter by status (done, pending, failed)
        res_status = params.get('status')
        if res_status:
            queryset = queryset.filter(status=res_status.lower())

        return queryset


class ResultSummaryAPIView(APIView):
    """
    GET /api/results/summary/ - Aggregate KPI metrics for top summary cards.
    Calculates: Total, Processed, Approved, Needing Review, and Failed counts in one query.
    """
    def get(self, request):
        queryset = ClassificationResult.objects.select_related('product', 'predicted_category', 'job')
        params = request.query_params

        job_id = params.get('job')
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        needs_review = params.get('needs_review') or params.get('needs_manual_review')
        if needs_review is not None:
            if needs_review.lower() in ('true', '1', 'yes'):
                queryset = queryset.filter(needs_manual_review=True)
            elif needs_review.lower() in ('false', '0', 'no'):
                queryset = queryset.filter(needs_manual_review=False)

        min_conf = params.get('min_confidence')
        if min_conf:
            try:
                queryset = queryset.filter(confidence__gte=float(min_conf))
            except ValueError:
                pass

        search = params.get('category') or params.get('search')
        if search:
            queryset = queryset.filter(
                Q(predicted_category_id=search) |
                Q(predicted_category__name__icontains=search) |
                Q(predicted_category__full_name__icontains=search) |
                Q(product__product_number__icontains=search) |
                Q(product__product_name__icontains=search) |
                Q(product__product_category__icontains=search) |
                Q(product__product_sub_category__icontains=search) |
                Q(product__materials__icontains=search)
            )

        # High performance aggregation using SQL Conditional Expressions
        counts = queryset.aggregate(
            total=Count('id'),
            processed=Count('id', filter=Q(status__in=[
                ClassificationResult.Status.DONE,
                ClassificationResult.Status.FAILED,
            ])),
            approved=Count('id', filter=Q(approved=True)),
            needs_review=Count('id', filter=Q(needs_manual_review=True)),
            failed=Count('id', filter=Q(status=ClassificationResult.Status.FAILED)),
        )

        return Response({
            'total': counts['total'] or 0,
            'processed': counts['processed'] or 0,
            'approved': counts['approved'] or 0,
            'needsReview': counts['needs_review'] or 0,
            'failed': counts['failed'] or 0,
        })


class ResultDetailUpdateAPIView(APIView):
    """
    GET   /api/results/{id}/ - Single result detail including alternatives and attributes.
    PATCH /api/results/{id}/ - In-place curator actions (Approve, Category Override, Reviewer).
    """
    def get_object(self, pk):
        return generics.get_object_or_404(
            ClassificationResult.objects.select_related('product', 'predicted_category', 'job'),
            pk=pk
        )

    def get(self, request, pk):
        result = self.get_object(pk)
        serializer = ClassificationResultDetailSerializer(result)
        return Response(serializer.data)

    def patch(self, request, pk):
        result = self.get_object(pk)
        input_serializer = ClassificationResultUpdateSerializer(data=request.data)
        input_serializer.is_valid(raise_exception=True)

        override_cat_id = input_serializer.validated_data.get('override_category_id')
        approved = input_serializer.validated_data.get('approved')
        reviewed_by = input_serializer.validated_data.get('reviewed_by')

        # 1. Apply category override if selected by curator
        if override_cat_id is not None:
            if override_cat_id:
                category_obj = Category.objects.get(id=override_cat_id)
                result.predicted_category = category_obj
            else:
                result.predicted_category = None

        # 2. Apply approval state
        if approved is not None:
            result.approved = approved
            if approved:
                # Approving an item clears the manual review flag
                result.needs_manual_review = False

        # 3. Apply curator username
        if reviewed_by is not None:
            result.reviewed_by = reviewed_by or (request.user.username if request.user.is_authenticated else "curator")

        result.save()

        detail_serializer = ClassificationResultDetailSerializer(result)
        return Response(detail_serializer.data, status=status.HTTP_200_OK)
