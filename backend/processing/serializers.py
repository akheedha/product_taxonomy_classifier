"""
Serializers for Processing Jobs.
"""

from rest_framework import serializers
from .models import ClassificationJob


class ClassificationJobSerializer(serializers.ModelSerializer):
    progress_percentage = serializers.ReadOnlyField()
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


class CreateJobRequestSerializer(serializers.Serializer):
    limit = serializers.IntegerField(required=False, default=0, min_value=0)
    sync = serializers.BooleanField(required=False, default=False)
