"""
REST API views for Catalog Upload and Ingestion.
"""

import os
import tempfile
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import CatalogImport
from .serializers import CatalogImportSerializer, CatalogImportUploadSerializer
from .services import ImportService


class ProductImportAPIView(APIView):
    """
    POST /api/imports/upload/
    Uploads .xlsx, .xls, .xlsm, or .csv spreadsheet and imports catalog records.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = CatalogImportUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = request.FILES.get('file')
        sheet_raw = request.data.get('sheet', 0)
        sheet = 0
        if isinstance(sheet_raw, str):
            sheet_raw = sheet_raw.strip()
            if sheet_raw.isdigit():
                sheet = int(sheet_raw)
            elif sheet_raw:
                sheet = sheet_raw

        suffix = os.path.splitext(uploaded_file.name)[1].lower()
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                temp_path = tmp.name
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)

            result = ImportService.import_catalog_file(
                file_path=temp_path,
                original_filename=uploaded_file.name,
                sheet=sheet,
            )

            return Response({
                'detail': 'Product catalog imported successfully.',
                'filename': uploaded_file.name,
                'result': result,
            }, status=status.HTTP_201_CREATED)

        except Exception as exc:
            return Response(
                {
                    'detail': 'Product import failed.',
                    'error': str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


class CatalogImportHistoryAPIView(generics.ListAPIView):
    """
    GET /api/imports/
    Lists past catalog spreadsheet import audits.
    """
    queryset = CatalogImport.objects.all()
    serializer_class = CatalogImportSerializer
