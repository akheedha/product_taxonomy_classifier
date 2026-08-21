"""
Validators for catalog spreadsheet rows and files.
"""

import os
from typing import Dict, Any, List, Tuple
from common.exceptions import CatalogImportError

ALLOWED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.xlsm'}


def validate_file_extension(filename: str) -> None:
    """Validates that the file has a supported spreadsheet extension."""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise CatalogImportError(
            f"Unsupported file format '{ext}'. Supported formats: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def validate_product_row(row: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validates mandatory SKU / Product Number for a row.
    Returns (is_valid, error_reason).
    """
    prod_num = row.get('product_number')
    if not prod_num or not str(prod_num).strip() or str(prod_num).strip().lower() in ('nan', 'none', 'null'):
        return False, "Missing mandatory SKU / Product Number"
    return True, ""
