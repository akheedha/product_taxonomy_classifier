"""
================================================================================
PRODUCT CATALOG INGESTION & DATA QUALITY AUDIT COMMAND
================================================================================
Purpose:
  Imports raw e-commerce product catalog spreadsheets (.xlsx, .xls, .xlsm, .csv)
  into the MariaDB/MySQL database. Performs column header normalization, currency
  parsing, image list aggregation (up to 20 images per SKU), bulk upserts, and
  generates a comprehensive data quality audit.

Usage:
  python manage.py import_products /path/to/catalog.xlsx --sheet=0 --batch-size=1000
"""

import os
import re
import sys
import time
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, List, Optional, Tuple

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from catalog.models import Product


class Command(BaseCommand):
    help = "Import catalog products from an .xlsx, .xls, or .csv spreadsheet file."

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            nargs='?',
            type=str,
            help="Path to the Excel (.xlsx/.xls) or CSV spreadsheet file to import."
        )
        parser.add_argument(
            '--file',
            type=str,
            dest='file_opt',
            help="Alternative flag to specify spreadsheet file path."
        )
        parser.add_argument(
            '--sheet',
            type=str,
            default=0,
            help="Sheet name or index to read from Excel file (default: first sheet / 0)"
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help="Batch size for database bulk operations (default: 1000)"
        )

    def handle(self, *args, **options):
        """
        Main execution workflow:
          1. Reads spreadsheet via Pandas (Excel or CSV).
          2. Normalizes column headers and detects image columns (Image 1 ... Image 20).
          3. Iterates over rows, extracts and cleans fields, tracking data quality metrics.
          4. Performs atomic bulk upsert into MariaDB/MySQL.
          5. Outputs summary and data quality audit report.
        """
        start_time = time.time()
        file_path_str = options['file_opt'] or options['file_path']

        if not file_path_str:
            raise CommandError("Please provide a file path: python manage.py import_products <path_to_file.xlsx>")

        file_path = Path(file_path_str).resolve()
        if not file_path.exists():
            raise CommandError(f"File not found: {file_path}")

        self.stdout.write(self.style.MIGRATE_HEADING(f"=== Importing Products from {file_path.name} ==="))
        self.stdout.write(f"Reading file: {file_path}")

        # ----------------------------------------------------------------------
        # 1. Load spreadsheet into Pandas DataFrame
        # ----------------------------------------------------------------------
        try:
            if file_path.suffix.lower() in ('.xlsx', '.xls', '.xlsm'):
                df = pd.read_excel(file_path, sheet_name=options['sheet'])
            elif file_path.suffix.lower() == '.csv':
                df = pd.read_csv(file_path, low_memory=False)
            else:
                raise CommandError(f"Unsupported file format '{file_path.suffix}'. Expected .xlsx, .xls, or .csv.")
        except Exception as e:
            raise CommandError(f"Failed to read spreadsheet file: {e}")

        total_rows_in_file = len(df)
        self.stdout.write(f"Loaded {total_rows_in_file:,} rows from spreadsheet.")

        # ----------------------------------------------------------------------
        # 2. Normalize column headers
        # ----------------------------------------------------------------------
        column_map = {str(col).strip(): col for col in df.columns}
        df.columns = [str(col).strip() for col in df.columns]

        # ----------------------------------------------------------------------
        # 3. Detect image columns (e.g. Image 1, Image 2, ..., Image 20)
        # ----------------------------------------------------------------------
        image_columns = [
            f"Image {i}" for i in range(1, 21) if f"Image {i}" in df.columns
        ]
        if not image_columns:
            image_columns = [col for col in df.columns if re.match(r'^Image\s*\d+$', col, re.IGNORECASE)]

        # ----------------------------------------------------------------------
        # 4. Parse rows & track data quality metrics
        # ----------------------------------------------------------------------
        self.stdout.write("Parsing rows and calculating data quality metrics...")
        product_objs = []
        skipped_count = 0

        # Data quality tracking counters
        missing_description_count = 0
        missing_images_count = 0
        missing_category_count = 0
        missing_sub_category_count = 0
        missing_name_count = 0
        missing_price_count = 0

        for index, row in df.iterrows():
            # Validate Product Number (mandatory unique SKU identifier)
            raw_prod_num = self._clean_str(row.get('Product Number'))
            if not raw_prod_num:
                skipped_count += 1
                continue

            # Extract and sanitize fields
            model_number = self._clean_str(row.get('Model Number'))
            product_category = self._clean_str(row.get('Product Category'))
            product_sub_category = self._clean_str(row.get('Product Sub Category'))
            collection_name = self._clean_str(row.get('Collection Name'))
            color_collection = self._clean_str(row.get('Color Collection'))
            product_color = self._clean_str(row.get('Product Color'))
            product_name = self._clean_str(row.get('Product Name'))
            brand = self._first_clean(row, ['Brand', 'Vendor', 'Manufacturer'])
            product_description = self._clean_str(row.get('Product Description'))
            bullets = self._clean_str(row.get('Bullets'))
            set_includes = self._clean_str(row.get('Set Includes'))
            product_weight = self._clean_str(row.get('Product Weight'))
            materials = self._clean_str(row.get('Materials'))
            product_dimensions = self._clean_str(row.get('Product Dimensions'))
            assembly_required = self._clean_str(row.get('Assembly Required'))
            is_set = self._clean_str(row.get('Is a Set'))
            stackable = self._clean_str(row.get('Stackable'))
            country_of_origin = self._clean_str(row.get('Country Of Origin'))

            # Parse pricing into Decimals
            item_cost = self._parse_decimal(row.get('Item Cost'))
            map_price = self._parse_decimal(row.get('MAP'))
            msrp = self._parse_decimal(row.get('MSRP'))

            # Aggregate all valid image URLs into a JSON list
            images = self._extract_images(row, image_columns)

            shipping_method = self._clean_str(row.get('Shipping Method'))
            total_box_count = self._clean_str(row.get('Total Box Count'))
            pallet_count = self._clean_str(row.get('Pallet Count'))
            shipping_weight = self._clean_str(row.get('Shipping Weight'))
            total_cbm = self._clean_str(row.get('Total CBM'))
            package_dimensions = self._clean_str(row.get('Package Dimensions'))
            product_url = self._clean_str(row.get('Product URL'))

            # Quality metric tracking
            if not product_description:
                missing_description_count += 1
            if not images:
                missing_images_count += 1
            if not product_category:
                missing_category_count += 1
            if not product_sub_category:
                missing_sub_category_count += 1
            if not product_name:
                missing_name_count += 1
            if msrp is None and map_price is None and item_cost is None:
                missing_price_count += 1

            product_objs.append(
                Product(
                    product_number=raw_prod_num,
                    model_number=model_number,
                    product_category=product_category,
                    product_sub_category=product_sub_category,
                    collection_name=collection_name,
                    color_collection=color_collection,
                    product_color=product_color,
                    product_name=product_name,
                    brand=brand,
                    product_description=product_description,
                    bullets=bullets,
                    set_includes=set_includes,
                    product_weight=product_weight,
                    materials=materials,
                    product_dimensions=product_dimensions,
                    assembly_required=assembly_required,
                    is_set=is_set,
                    stackable=stackable,
                    country_of_origin=country_of_origin,
                    item_cost=item_cost,
                    map_price=map_price,
                    msrp=msrp,
                    images=images,
                    shipping_method=shipping_method,
                    total_box_count=total_box_count,
                    pallet_count=pallet_count,
                    shipping_weight=shipping_weight,
                    total_cbm=total_cbm,
                    package_dimensions=package_dimensions,
                    product_url=product_url,
                )
            )

        total_valid = len(product_objs)
        self.stdout.write(f"Parsed {total_valid:,} valid products ({skipped_count:,} skipped due to missing product number).")

        # ----------------------------------------------------------------------
        # 5. Bulk upsert into MariaDB/MySQL
        # ----------------------------------------------------------------------
        self.stdout.write("Writing products to database (bulk upsert)...")
        update_fields = [
            'model_number',
            'product_category',
            'product_sub_category',
            'collection_name',
            'color_collection',
            'product_color',
            'product_name',
            'brand',
            'product_description',
            'bullets',
            'set_includes',
            'product_weight',
            'materials',
            'product_dimensions',
            'assembly_required',
            'is_set',
            'stackable',
            'country_of_origin',
            'item_cost',
            'map_price',
            'msrp',
            'images',
            'shipping_method',
            'total_box_count',
            'pallet_count',
            'shipping_weight',
            'total_cbm',
            'package_dimensions',
            'product_url',
        ]

        batch_size = options['batch_size']
        with transaction.atomic():
            Product.objects.bulk_create(
                product_objs,
                batch_size=batch_size,
                update_conflicts=True,
                update_fields=update_fields
            )

        db_count = Product.objects.count()
        duration = time.time() - start_time

        # ----------------------------------------------------------------------
        # 6. Report Data Quality & Import Summary
        # ----------------------------------------------------------------------
        self.stdout.write(self.style.SUCCESS("\n=== Product Import Summary ==="))
        self.stdout.write(f"  - Total spreadsheet rows:        {total_rows_in_file:,}")
        self.stdout.write(f"  - Rows skipped (no SKU):         {skipped_count:,}")
        self.stdout.write(f"  - Products imported/updated:     {total_valid:,}")
        self.stdout.write(f"  - Total Products in Database:    {db_count:,}")
        self.stdout.write(f"  - Execution time:                {duration:.2f} seconds")

        self.stdout.write(self.style.WARNING("\n=== Data Quality Audit ==="))
        self._print_quality_metric("Missing Description", missing_description_count, total_valid)
        self._print_quality_metric("Missing Images (empty list)", missing_images_count, total_valid)
        self._print_quality_metric("Missing Product Category", missing_category_count, total_valid)
        self._print_quality_metric("Missing Sub-Category", missing_sub_category_count, total_valid)
        self._print_quality_metric("Missing Product Name", missing_name_count, total_valid)
        self._print_quality_metric("Missing Price (all pricing null)", missing_price_count, total_valid)
        self.stdout.write(self.style.SUCCESS("\nProduct import completed successfully!"))

    def _print_quality_metric(self, label: str, count: int, total: int):
        """Helper to format and print a quality metric percentage bar."""
        pct = (count / total * 100) if total > 0 else 0.0
        flag = " [!]" if count > 0 else " [OK]"
        self.stdout.write(f"  - {label:<35}: {count:>6,} / {total:,} ({pct:>5.1f}%){flag}")

    def _clean_str(self, val: Any) -> Optional[str]:
        """Clean string, strip whitespace, handle NaN / null / XML formatting artifacts."""
        if pd.isna(val) or val is None:
            return None
        text = str(val).strip()
        if not text or text.lower() in ('nan', 'null', 'none'):
            return None
        text = text.replace('_x000D_\n', '\n').replace('_x000D_', '\n')
        return text

    def _first_clean(self, row: Any, columns: List[str]) -> Optional[str]:
        """Returns first non-empty cleaned value from list of alternative column names."""
        for col in columns:
            value = self._clean_str(row.get(col))
            if value:
                return value
        return None

    def _parse_decimal(self, val: Any) -> Optional[Decimal]:
        """Parses float, int, or currency string (e.g. '$129.99') into Decimal."""
        if pd.isna(val) or val is None:
            return None
        try:
            if isinstance(val, (int, float)):
                return Decimal(str(round(val, 2)))
            cleaned = str(val).strip().replace('$', '').replace(',', '')
            if not cleaned or cleaned.lower() in ('nan', 'null', 'none'):
                return None
            return Decimal(cleaned).quantize(Decimal('0.01'))
        except (InvalidOperation, ValueError):
            return None

    def _extract_images(self, row: Any, image_columns: List[str]) -> List[str]:
        """Extracts up to 20 valid image URLs from dynamic image columns."""
        images = []
        for col in image_columns:
            val = row.get(col)
            if pd.notna(val) and val is not None:
                text = str(val).strip()
                if text.startswith(('http://', 'https://', '//', 'data:image')) or re.search(r'\.(jpg|jpeg|png|webp|gif)$', text, re.IGNORECASE):
                    images.append(text)
        return images
