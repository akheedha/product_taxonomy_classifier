import io
import pandas as pd
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Product


class ImportAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_upload_csv_catalog(self):
        df = pd.DataFrame({
            'Product Number': ['API-UPLOAD-1', 'API-UPLOAD-2'],
            'Product Name': ['Velvet Armchair', 'Marble End Table'],
            'Brand': ['LivingLux', 'LivingLux'],
            'Image 1': ['https://example.com/a1.jpg', 'https://example.com/a2.jpg'],
        })
        csv_buffer = io.BytesIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        uploaded_file = SimpleUploadedFile(
            'test_catalog.csv',
            csv_buffer.getvalue(),
            content_type='text/csv'
        )

        response = self.client.post(
            '/api/imports/upload/',
            {'file': uploaded_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.filter(product_number='API-UPLOAD-1').count(), 1)
        self.assertEqual(Product.objects.filter(product_number='API-UPLOAD-2').count(), 1)
