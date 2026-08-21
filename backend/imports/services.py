"""
Catalog Ingestion Service layer.
"""

import os
import time
import logging
from typing import Dict, Any, List, Optional
from django.db import transaction
from products.models import Product
from .models import CatalogImport
from .excel_parser import ExcelCatalogParser
from .validators import validate_file_extension

logger = logging.getLogger(__name__)


class ImportService:
    """
    Orchestrates spreadsheet parsing, product bulk upserts, and data quality logging.
    """

    @classmethod
    def import_catalog_file(
        cls,
        file_path: str,
        original_filename: Optional[str] = None,
        sheet: Any = 0,
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        start_time = time.time()
        filename = original_filename or os.path.basename(file_path)
        validate_file_extension(filename)

        import_log = CatalogImport.objects.create(
            filename=filename,
            sheet_name=str(sheet),
            status=CatalogImport.Status.PENDING
        )

        try:
            records, metrics, total_rows = ExcelCatalogParser.parse_file(file_path, sheet=sheet)
            import_log.total_rows = total_rows
            import_log.skipped_count = metrics.get('skipped_empty_rows', 0)

            # Atomic bulk upsert into products table
            imported_count = cls._bulk_upsert_products(records, batch_size=batch_size)

            import_log.imported_count = imported_count
            import_log.data_quality_metrics = metrics
            import_log.status = (
                CatalogImport.Status.SUCCESS if imported_count > 0 else CatalogImport.Status.PARTIAL
            )
            import_log.save()

            elapsed = round(time.time() - start_time, 2)
            logger.info(f"Import #{import_log.id} finished: {imported_count} products in {elapsed}s")

            return {
                'import_id': import_log.id,
                'filename': filename,
                'status': import_log.status,
                'total_rows': total_rows,
                'imported_count': imported_count,
                'skipped_count': import_log.skipped_count,
                'data_quality_metrics': metrics,
                'elapsed_seconds': elapsed,
            }

        except Exception as exc:
            logger.exception(f"Catalog import failed for {filename}: {exc}")
            import_log.status = CatalogImport.Status.FAILED
            import_log.error_message = str(exc)
            import_log.save()
            raise

    @classmethod
    def _bulk_upsert_products(cls, records: List[Dict[str, Any]], batch_size: int = 1000) -> int:
        if not records:
            return 0

        # Collect unique SKUs to resolve conflicts
        skus = [r['product_number'] for r in records if r.get('product_number')]
        existing_products = {
            p.product_number: p
            for p in Product.objects.filter(product_number__in=skus)
        }

        to_create = []
        to_update = []

        update_fields = [
            'model_number', 'product_category', 'product_sub_category',
            'collection_name', 'color_collection', 'product_color',
            'product_name', 'brand', 'product_description', 'bullets',
            'set_includes', 'product_weight', 'materials', 'product_dimensions',
            'assembly_required', 'is_set', 'stackable', 'country_of_origin',
            'item_cost', 'map_price', 'msrp', 'images', 'shipping_method',
            'total_box_count', 'pallet_count', 'shipping_weight', 'total_cbm',
            'package_dimensions', 'product_url'
        ]

        for r in records:
            sku = r['product_number']
            if sku in existing_products:
                prod = existing_products[sku]
                for field in update_fields:
                    setattr(prod, field, r.get(field))
                to_update.append(prod)
            else:
                to_create.append(Product(**r))

        with transaction.atomic():
            if to_create:
                Product.objects.bulk_create(to_create, batch_size=batch_size, ignore_conflicts=True)
            if to_update:
                Product.objects.bulk_update(to_update, fields=update_fields, batch_size=batch_size)

        return len(to_create) + len(to_update)
