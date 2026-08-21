"""
Shared utilities for networking, text sanitization, and database helpers.
"""

import re
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, List, Dict, Any


def get_http_session_with_retries(
    max_retries: int = 2,
    backoff_factor: float = 0.3,
    status_forcelist: tuple = (500, 502, 503, 504)
) -> requests.Session:
    """
    Creates and returns a requests.Session with connection pooling and automated exponential retries.
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=status_forcelist,
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retry_strategy, pool_connections=10, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session


def clean_string(val: Any) -> Optional[str]:
    """
    Sanitizes string inputs, stripping excess whitespace and treating 'nan'/'none' as None.
    """
    if val is None:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ('nan', 'none', 'null', 'n/a'):
        return None
    return val_str


def extract_title_brand_model(title: str) -> Dict[str, str]:
    """
    Strips SKU-like codes and normalizes product title strings.
    """
    if not title:
        return {"clean_title": "", "extracted_sku": ""}

    cleaned = re.sub(r'^[A-Z0-9\-]{4,}\s+', '', title).strip()
    sku_match = re.search(r'^[A-Z0-9\-]{4,}', title)
    extracted_sku = sku_match.group(0) if sku_match else ""

    return {
        "clean_title": cleaned or title,
        "extracted_sku": extracted_sku
    }
