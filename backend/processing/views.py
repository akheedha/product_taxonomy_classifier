"""
REST API views for Job creation, tracking, and execution.
"""

from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import ClassificationJob
from .serializers import ClassificationJobSerializer, CreateJobRequestSerializer
from .services import ProcessingService


class JobListCreateAPIView(generics.ListCreateAPIView):
    """
    GET  /api/jobs/  -> Lists historical batch runs.
    POST /api/jobs/  -> Queues and dispatches a new batch classification job.
    """
    queryset = ClassificationJob.objects.all()
    serializer_class = ClassificationJobSerializer

    def create(self, request, *args, **kwargs):
        serializer = CreateJobRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        limit = serializer.validated_data.get('limit', 0)
        sync = serializer.validated_data.get('sync', False)

        job = ProcessingService.create_and_dispatch_job(
            limit=limit if limit > 0 else None,
            sync=sync
        )

        job_serializer = ClassificationJobSerializer(job)
        return Response(job_serializer.data, status=status.HTTP_201_CREATED)


class JobDetailAPIView(generics.RetrieveAPIView):
    """
    GET /api/jobs/{id}/ -> Real-time status, progress, and timing of a specific job.
    """
    queryset = ClassificationJob.objects.all()
    serializer_class = ClassificationJobSerializer


class JobResumeAPIView(APIView):
    """
    POST /api/jobs/{id}/resume/ -> Resumes interrupted or incomplete job.
    """
    def post(self, request, pk):
        job = ProcessingService.resume_job(job_id=pk, sync=request.data.get('sync', False))
        if not job:
            return Response({'detail': f'Job #{pk} not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ClassificationJobSerializer(job).data)
