import tempfile
import pandas as pd
from django.test import TestCase
from imports.excel_parser import ExcelCatalogParser


class ExcelParserTests(TestCase):
    def test_parse_csv_file(self):
        data = {
            'Product Number': ['TEST-1', 'TEST-2'],
            'Product Name': ['Wooden Chair', 'Glass Coffee Table'],
            'Brand': ['Acme', 'Nordic'],
            'Image 1': ['https://example.com/img1.jpg', 'https://example.com/img2.jpg'],
            'Image 2': ['https://example.com/img1b.jpg', ''],
            'MSRP': ['$199.99', '299.50']
        }
        df = pd.DataFrame(data)

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False, mode='w', newline='') as f:
            df.to_csv(f.name, index=False)
            temp_path = f.name

        records, metrics, total = ExcelCatalogParser.parse_file(temp_path)
        self.assertEqual(total, 2)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0]['product_number'], 'TEST-1')
        self.assertEqual(len(records[0]['images']), 2)
        self.assertEqual(records[0]['images'][0], 'https://example.com/img1.jpg')
        self.assertEqual(float(records[0]['msrp']), 199.99)
