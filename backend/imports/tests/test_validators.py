from django.test import TestCase
from common.exceptions import CatalogImportError
from imports.validators import validate_file_extension, validate_product_row


class ImportValidatorTests(TestCase):
    def test_valid_extensions(self):
        for name in ['catalog.xlsx', 'catalog.xls', 'products.csv', 'items.xlsm']:
            try:
                validate_file_extension(name)
            except CatalogImportError:
                self.fail(f"validate_file_extension raised error unexpectedly for {name}")

    def test_invalid_extension(self):
        with self.assertRaises(CatalogImportError):
            validate_file_extension('catalog.pdf')

    def test_validate_product_row_valid(self):
        valid, _ = validate_product_row({'product_number': 'SKU-100'})
        self.assertTrue(valid)

    def test_validate_product_row_missing_sku(self):
        valid, reason = validate_product_row({'product_name': 'Chair without SKU'})
        self.assertFalse(valid)
        self.assertIn('Missing mandatory SKU', reason)
