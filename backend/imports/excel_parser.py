"""
Excel and CSV catalog spreadsheet parser.
"""

import os
import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from common.exceptions import CatalogImportError
from common.utils import clean_string


class ExcelCatalogParser:
    """
    Parses product catalog spreadsheets (.xlsx, .xls, .csv), normalizes columns,
    aggregates multi-image columns, and prepares sanitized product record dictionaries.
    """

    @classmethod
    def parse_file(
        cls,
        file_path: str,
        sheet: Any = 0
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], int]:
        """
        Parses a spreadsheet file from disk and returns:
          (sanitized_product_dicts, data_quality_metrics, total_rows_in_file)
        """
        ext = os.path.splitext(file_path)[1].lower()
        try:
            if ext in ('.xlsx', '.xls', '.xlsm'):
                df = pd.read_excel(file_path, sheet_name=sheet)
            elif ext == '.csv':
                df = pd.read_csv(file_path, low_memory=False)
            else:
                raise CatalogImportError(f"Unsupported extension: {ext}")
        except Exception as exc:
            raise CatalogImportError(f"Failed to read spreadsheet file: {exc}")

        total_rows = len(df)
        df.columns = [str(col).strip() for col in df.columns]

        # Detect image columns
        image_columns = [f"Image {i}" for i in range(1, 21) if f"Image {i}" in df.columns]
        if not image_columns:
            image_columns = [col for col in df.columns if re.match(r'^Image\s*\d+$', col, re.IGNORECASE)]

        parsed_records = []
        skipped_count = 0

        # Metrics counters
        missing_desc = 0
        missing_images = 0
        missing_category = 0
        missing_price = 0

        for _, row in df.iterrows():
            prod_num = clean_string(row.get('Product Number') or row.get('SKU') or row.get('Item #'))
            if not prod_num:
                skipped_count += 1
                continue

            # Gather image URLs
            images = []
            for col in image_columns:
                img_url = clean_string(row.get(col))
                if img_url and img_url not in images:
                    images.append(img_url)

            # Check primary image fallback if named 'Image' or 'Photo'
            if not images and 'Image' in df.columns:
                img_url = clean_string(row.get('Image'))
                if img_url:
                    images.append(img_url)

            desc = clean_string(row.get('Product Description') or row.get('Description'))
            cat = clean_string(row.get('Product Category') or row.get('Category'))
            sub_cat = clean_string(row.get('Product Sub Category') or row.get('Sub Category'))
            brand = (
                clean_string(row.get('Brand')) or
                clean_string(row.get('Vendor')) or
                clean_string(row.get('Manufacturer'))
            )

            cost = cls._parse_decimal(row.get('Item Cost') or row.get('Cost'))
            map_price = cls._parse_decimal(row.get('Map Price') or row.get('MAP'))
            msrp = cls._parse_decimal(row.get('MSRP') or row.get('Price'))

            if not desc:
                missing_desc += 1
            if not images:
                missing_images += 1
            if not cat and not sub_cat:
                missing_category += 1
            if cost is None and map_price is None and msrp is None:
                missing_price += 1

            record = {
                'product_number': prod_num,
                'model_number': clean_string(row.get('Model Number')),
                'product_category': cat,
                'product_sub_category': sub_cat,
                'collection_name': clean_string(row.get('Collection Name')),
                'color_collection': clean_string(row.get('Color Collection')),
                'product_color': clean_string(row.get('Product Color') or row.get('Color')),
                'product_name': clean_string(row.get('Product Name') or row.get('Title') or row.get('Name')),
                'brand': brand,
                'product_description': desc,
                'bullets': clean_string(row.get('Bullets')),
                'set_includes': clean_string(row.get('Set Includes')),
                'product_weight': clean_string(row.get('Product Weight') or row.get('Weight')),
                'materials': clean_string(row.get('Materials') or row.get('Material')),
                'product_dimensions': clean_string(row.get('Product Dimensions') or row.get('Dimensions')),
                'assembly_required': clean_string(row.get('Assembly Required')),
                'is_set': clean_string(row.get('Is a Set')),
                'stackable': clean_string(row.get('Stackable')),
                'country_of_origin': clean_string(row.get('Country of Origin')),
                'item_cost': cost,
                'map_price': map_price,
                'msrp': msrp,
                'images': images,
                'shipping_method': clean_string(row.get('Shipping Method')),
                'total_box_count': clean_string(row.get('Total Box Count')),
                'pallet_count': clean_string(row.get('Pallet Count')),
                'shipping_weight': clean_string(row.get('Shipping Weight')),
                'total_cbm': clean_string(row.get('Total CBM')),
                'package_dimensions': clean_string(row.get('Package Dimensions')),
                'product_url': clean_string(row.get('Product URL') or row.get('URL')),
            }
            parsed_records.append(record)

        quality_metrics = {
            'total_rows_in_file': total_rows,
            'valid_records_parsed': len(parsed_records),
            'skipped_empty_rows': skipped_count,
            'missing_description_count': missing_desc,
            'missing_images_count': missing_images,
            'missing_category_count': missing_category,
            'missing_price_count': missing_price,
        }

        return parsed_records, quality_metrics, total_rows

    @staticmethod
    def _parse_decimal(val: Any) -> Optional[Decimal]:
        """Safely parses currency / numeric values into Decimal."""
        if val is None:
            return None
        cleaned = re.sub(r'[^\d.]', '', str(val).strip())
        if not cleaned:
            return None
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
