"""
Serializers for Catalog Ingestion.
"""

from rest_framework import serializers
from .models import CatalogImport


class CatalogImportSerializer(serializers.ModelSerializer):
    class Meta:
        model = CatalogImport
        fields = '__all__'


class CatalogImportUploadSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    sheet = serializers.CharField(required=False, default='0')
    batch_size = serializers.IntegerField(required=False, default=1000)
