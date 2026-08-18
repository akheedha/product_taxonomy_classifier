import os
import tempfile
from io import StringIO

from django.core.management import call_command
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView


class ProductImportAPIView(APIView):
    """
    Upload a CSV/XLS/XLSX product catalog and import it using the same parser as
    the management command.
    """
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        sheet = request.data.get('sheet', 0)
        if isinstance(sheet, str):
            sheet = sheet.strip()
            if sheet == '':
                sheet = 0
            elif sheet.isdigit():
                sheet = int(sheet)

        if not uploaded_file:
            return Response(
                {'detail': 'Upload a product file using the "file" field.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        suffix = os.path.splitext(uploaded_file.name)[1].lower()
        if suffix not in {'.csv', '.xlsx', '.xls', '.xlsm'}:
            return Response(
                {'detail': 'Unsupported file type. Upload .csv, .xlsx, .xls, or .xlsm.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        temp_path = None
        output = StringIO()
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                temp_path = tmp.name
                for chunk in uploaded_file.chunks():
                    tmp.write(chunk)

            call_command(
                'import_products',
                temp_path,
                sheet=sheet,
                stdout=output,
            )

            return Response({
                'detail': 'Product catalog imported successfully.',
                'filename': uploaded_file.name,
                'log': output.getvalue(),
            })
        except Exception as exc:
            return Response(
                {
                    'detail': 'Product import failed.',
                    'error': str(exc),
                    'log': output.getvalue(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
