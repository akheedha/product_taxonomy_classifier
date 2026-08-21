"""
================================================================================
ATTRIBUTE EXTRACTION ENGINE (RAPIDFUZZ + TAXONOMY SCHEMA)
================================================================================
Purpose:
  Extracts taxonomy-specific attributes (e.g. Color, Material, Pattern, Furniture Style)
  from product titles, descriptions, and metadata, mapping them strictly to Shopify's
  canonical allowed attribute values.

Core Technology:
  - Exact Word-Boundary Regex: r'\b' + re.escape(value) + r'\b' for 100% precision.
  - Fuzzy Matching (RapidFuzz): Uses C++ accelerated fuzzy partial string ratio matching
    to tolerate spelling differences and plurals (e.g. "Teak Woods" -> "Teak Wood").
  - Field-Specific Priority Hints: Checks dedicated catalog columns (e.g., 'product_color'
    for Color, 'materials' for Material) before searching general descriptions.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Union

from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# Minimum fuzzy similarity score (0 to 100) required to accept a matched attribute value
DEFAULT_SIMILARITY_THRESHOLD: float = 80.0

# Mapping attribute names to specific catalog columns for prioritized matching
ATTRIBUTE_FIELD_HINTS = {
    'color': ['product_color', 'color', 'color_collection'],
    'material': ['materials', 'material'],
    'materials': ['materials', 'material'],
    'pattern': ['collection_name', 'product_name', 'title'],
    'room': ['product_category', 'product_sub_category'],
}


def _get_field_val(product: Any, key: str) -> str:
    """Helper to retrieve string value from model instance or dictionary safely."""
    if isinstance(product, dict):
        val = product.get(key)
    else:
        val = getattr(product, key, None)
    return str(val).strip() if val is not None else ""


def _build_search_corpus(product: Any) -> str:
    """
    Synthesizes all product textual metadata into a single searchable text corpus.
    """
    fields = []
    for field_name in [
        'product_name', 'title',
        'brand', 'vendor', 'manufacturer',
        'product_color', 'color', 'color_collection',
        'materials', 'material',
        'bullets',
        'product_description', 'description',
        'collection_name',
        'product_category',
        'product_sub_category',
    ]:
        val = _get_field_val(product, field_name)
        if val:
            fields.append(val)

    return " | ".join(fields).strip()


def extract_attributes(
    product: Any,
    predicted_category: Any,
    similarity_threshold: float = DEFAULT_SIMILARITY_THRESHOLD
) -> Dict[str, Dict[str, Any]]:
    """
    Extracts category-specific attributes and allowed values for a product.

    Workflow:
      1. Resolves Category model instance.
      2. Fetches all valid Attribute schemas linked to this Category (and parent ancestors).
      3. For each Attribute (e.g. 'Material'), iterates over its canonical values (e.g. 'Teak', 'Oak').
      4. Checks dedicated field hints first, then tests exact regex match and RapidFuzz partial match.
      5. Selects the highest confidence match meeting the similarity threshold.

    Args:
        product: Django Product model instance or dict.
        predicted_category: Target Category model instance, dict with 'id', or Category ID string.
        similarity_threshold: Minimum match score (0-100) to accept an attribute value (default: 80.0).

    Returns:
        Dict: {attribute_name: {"value": canonical_value, "confidence": float(0.0 to 1.0)}}
    """
    if not product or not predicted_category:
        return {}

    try:
        from taxonomy.models import Attribute, Category

        # Step 1: Resolve Category model instance
        category_obj = None
        if isinstance(predicted_category, Category):
            category_obj = predicted_category
        elif isinstance(predicted_category, dict) and 'id' in predicted_category:
            category_obj = Category.objects.filter(id=predicted_category['id']).first()
        elif isinstance(predicted_category, str):
            category_obj = Category.objects.filter(id=predicted_category).first()

        if not category_obj:
            return {}

        # Step 2: Retrieve attributes assigned to category (or inherited from ancestors)
        attributes = list(category_obj.attributes.all().prefetch_related('values'))
        if not attributes:
            ancestor_ids = [a.id for a in category_obj.get_ancestors(include_self=False)]
            if ancestor_ids:
                attributes = list(
                    Attribute.objects.filter(categories__id__in=ancestor_ids)
                    .distinct()
                    .prefetch_related('values')
                )

        if not attributes:
            return {}

        # Step 3: Build product search text corpus
        search_corpus = _build_search_corpus(product)
        if not search_corpus:
            return {}

        search_corpus_lower = search_corpus.lower()
        extracted: Dict[str, Dict[str, Any]] = {}

        # Step 4: Evaluate each allowed attribute against the product
        for attr in attributes:
            attr_name_lower = attr.name.lower()
            best_match_val = None
            best_score = 0.0
            best_priority = False
            best_len = 0

            # Priority check in dedicated product fields
            hint_fields = ATTRIBUTE_FIELD_HINTS.get(attr_name_lower, [])
            dedicated_text = " ".join([_get_field_val(product, f).lower() for f in hint_fields if _get_field_val(product, f)])

            attr_values = list(attr.values.all())
            if not attr_values:
                continue

            for val_obj in attr_values:
                raw_val = val_obj.value
                val_lower = raw_val.lower().strip()
                if not val_lower or len(val_lower) < 2:
                    continue

                pattern = r'\b' + re.escape(val_lower) + r'\b'
                is_dedicated_match = bool(dedicated_text and re.search(pattern, dedicated_text))

                if is_dedicated_match or re.search(pattern, search_corpus_lower):
                    score = 100.0
                else:
                    # Fuzzy match with RapidFuzz partial ratio
                    score = float(fuzz.partial_ratio(val_lower, search_corpus_lower))

                if score >= similarity_threshold:
                    val_len = len(val_lower)
                    # Prefer dedicated column matches, higher scores, and more specific (longer) names
                    is_better = (
                        (is_dedicated_match and not best_priority) or
                        (is_dedicated_match == best_priority and score > best_score) or
                        (is_dedicated_match == best_priority and score == best_score and val_len > best_len)
                    )
                    if is_better:
                        best_score = score
                        best_match_val = raw_val
                        best_priority = is_dedicated_match
                        best_len = val_len

            if best_match_val and best_score >= similarity_threshold:
                extracted[attr.name] = {
                    "value": best_match_val,
                    "confidence": round(best_score / 100.0, 4)
                }

        return extracted

    except Exception as e:
        logger.warning(f"Error extracting attributes: {e}")
        return {}
