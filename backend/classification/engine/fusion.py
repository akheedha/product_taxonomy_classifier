"""
================================================================================
MULTIMODAL FUSION ENGINE FOR PRODUCT TAXONOMY CLASSIFICATION
================================================================================
Purpose:
  This module orchestrates the end-to-end classification pipeline for an e-commerce
  product. It integrates:
    1. Text Semantic Classification (using SentenceTransformers embeddings)
    2. Zero-Shot Visual Classification (using OpenCLIP image-text embeddings)
    3. Multimodal Score Fusion (Weighted Linear Combination)
    4. Smart Ambiguity & Confidence Heuristics (Flags ambiguous items for human curation)
    5. Attribute Extraction (Extracts materials, colors, styles using RapidFuzz)

Why Multimodal Fusion?
  - Text alone can be misled by generic titles or missing descriptions.
  - Image alone can confuse similar looking items (e.g., dining chair vs desk chair).
  - Combining text (60%) + image (40%) produces high accuracy and robust confidence scores.
"""

import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from .attribute_extractor import extract_attributes
from .image_classifier import classify_image
from .text_classifier import classify_text

logger = logging.getLogger(__name__)

# ==============================================================================
# PIPELINE CONFIGURATION & TUNABLE HEURISTIC THRESHOLDS
# ==============================================================================
# Feature Weights: Determines the relative contribution of text and image signals
TEXT_WEIGHT: float = 0.6   # 60% weight given to SentenceTransformers text similarity
IMAGE_WEIGHT: float = 0.4  # 40% weight given to OpenCLIP visual similarity

# Confidence & Review Thresholds:
# 1. CONFIDENCE_THRESHOLD: Products with overall confidence below 0.55 (55%) require human review.
CONFIDENCE_THRESHOLD: float = 0.55

# 2. AMBIGUITY_GAP_THRESHOLD: In Shopify's dense 14.6k taxonomy tree, if the top 2 category
#    candidates have a score difference < 0.01 (1.0%), it indicates borderline ambiguity.
AMBIGUITY_GAP_THRESHOLD: float = 0.01

# 3. HIGH_CONFIDENCE_AUTO_APPROVE: If overall confidence is >= 0.65 (65%), the prediction
#    is considered decisive and auto-approved, bypassing the sibling ambiguity flag.
HIGH_CONFIDENCE_AUTO_APPROVE: float = 0.65

# Top-K Candidate generation:
DEFAULT_TEXT_CANDIDATES_K: int = 5     # Retrieve top 5 candidates from text for visual re-ranking
MAX_ALTERNATIVE_CATEGORIES: int = 3    # Keep top 3 alternatives for curator review in UI


def classify_product(
    product: Any,
    text_weight: float = TEXT_WEIGHT,
    image_weight: float = IMAGE_WEIGHT,
    confidence_threshold: float = CONFIDENCE_THRESHOLD,
    ambiguity_gap_threshold: float = AMBIGUITY_GAP_THRESHOLD,
    high_confidence_auto_approve: float = HIGH_CONFIDENCE_AUTO_APPROVE,
    text_candidates_k: int = DEFAULT_TEXT_CANDIDATES_K
) -> Dict[str, Any]:
    """
    Executes the multimodal classification and attribute extraction pipeline for a single product.

    Pipeline Steps:
      Step 1: Text Embedding Classification -> Queries SentenceTransformers against 14,606 categories.
      Step 2: Image URL Extraction -> Finds primary image from product metadata.
      Step 3: OpenCLIP Visual Re-ranking -> Computes zero-shot image similarity on top text candidates.
      Step 4: Linear Fusion -> Calculates fused_score = (w_text * s_text) + (w_image * s_image).
      Step 5: Alternative Categories -> Retains top 3 alternative paths for curator inspection.
      Step 6: Ambiguity & Review Flagging -> Applies confidence & ambiguity gap heuristics.
      Step 7: Attribute Extraction -> Matches category-allowed attributes using RapidFuzz string distance.

    Args:
        product: Django Product model instance or dictionary of product attributes.
        text_weight: Weight multiplier for text embedding score (default: 0.60).
        image_weight: Weight multiplier for image embedding score (default: 0.40).
        confidence_threshold: Minimum score threshold for auto-approval (default: 0.55).
        ambiguity_gap_threshold: Minimum gap required between rank 1 and rank 2 predictions (default: 0.01).
        high_confidence_auto_approve: Score threshold above which ambiguity gap is bypassed (default: 0.65).
        text_candidates_k: Number of candidate categories generated from text stage (default: 5).

    Returns:
        Dict containing predicted category, confidence score, alternatives, extracted attributes,
        and review flags.
    """
    start_time = time.time()
    product_id = getattr(product, 'product_number', None) or (product.get('product_number') if isinstance(product, dict) else None)

    # --------------------------------------------------------------------------
    # STEP 1: Text-Based Semantic Classification
    # --------------------------------------------------------------------------
    # Builds rich query text (Title + Brand + Raw Categories + Materials + Description)
    # and computes cosine similarity with pre-indexed Shopify taxonomy embeddings.
    text_preds, text_meta = classify_text(product, top_k=text_candidates_k)
    is_low_info = text_meta.get('is_low_info', False)

    # Fallback if text classification yields no results
    if not text_preds:
        return {
            "predicted_category": None,
            "category_id": None,
            "name": None,
            "full_name": None,
            "confidence": 0.0,
            "alternative_categories": [],
            "extracted_attributes": {},
            "needs_manual_review": True,
            "review_reasons": ["Text classification produced 0 candidates"],
            "used_image": False,
            "image_url": None,
            "text_predictions": [],
            "image_predictions": [],
            "is_low_info": is_low_info,
            "status": "failed",
            "error": "No text predictions generated"
        }

    # --------------------------------------------------------------------------
    # STEP 2: Extract Primary Image URL for Vision Model
    # --------------------------------------------------------------------------
    image_url = None
    if hasattr(product, 'primary_image') and product.primary_image:
        image_url = product.primary_image
    elif hasattr(product, 'images') and isinstance(product.images, list) and len(product.images) > 0:
        image_url = product.images[0]
    elif isinstance(product, dict):
        imgs = product.get('images', [])
        if isinstance(imgs, list) and len(imgs) > 0:
            image_url = imgs[0]
        elif product.get('image_url'):
            image_url = product.get('image_url')

    # --------------------------------------------------------------------------
    # STEP 3: Zero-Shot Visual Classification (OpenCLIP)
    # --------------------------------------------------------------------------
    # Downloads product image and computes visual similarity against top text candidates.
    image_preds_raw = []
    used_image = False

    if image_url:
        image_preds_raw = classify_image(
            image_url=image_url,
            candidate_categories=text_preds,
            product_id=product_id
        )
        if image_preds_raw:
            used_image = True

    # --------------------------------------------------------------------------
    # STEP 4: Multimodal Linear Fusion
    # --------------------------------------------------------------------------
    # Combines text and image signals into a unified fused confidence score.
    fused_candidates = []
    image_score_map = {}
    for cat_item, img_score in image_preds_raw:
        cat_id = cat_item.get('category_id') if isinstance(cat_item, dict) else getattr(cat_item, 'id', str(cat_item))
        image_score_map[cat_id] = img_score

    for text_item in text_preds:
        cat_id = text_item['category_id']
        t_score = text_item['score']

        if used_image and cat_id in image_score_map:
            # Both signals available: compute weighted sum
            i_score = image_score_map[cat_id]
            fused_score = (text_weight * t_score) + (image_weight * i_score)
        else:
            # Fallback to text score if image is absent or download fails
            i_score = None
            fused_score = t_score

        fused_candidates.append({
            "category": text_item.get('category'),
            "category_id": cat_id,
            "name": text_item['name'],
            "full_name": text_item['full_name'],
            "level": text_item.get('level', 0),
            "text_score": round(t_score, 4),
            "image_score": round(i_score, 4) if i_score is not None else None,
            "fused_score": round(fused_score, 4),
        })

    # Sort all candidates by final fused score in descending order
    fused_candidates.sort(key=lambda x: x['fused_score'], reverse=True)

    top_candidate = fused_candidates[0]
    top_confidence = top_candidate['fused_score']

    # --------------------------------------------------------------------------
    # STEP 5: Alternative Categories (For Curator Review Dropdown in UI)
    # --------------------------------------------------------------------------
    alternative_categories = []
    for cand in fused_candidates[1:1 + MAX_ALTERNATIVE_CATEGORIES]:
        alternative_categories.append({
            "category_id": cand["category_id"],
            "name": cand["name"],
            "full_name": cand["full_name"],
            "score": cand["fused_score"],
        })

    # --------------------------------------------------------------------------
    # STEP 6: Manual Review Evaluation Heuristics
    # --------------------------------------------------------------------------
    needs_manual_review = False
    review_reasons = []

    # Heuristic A: Absolute Low Confidence Threshold
    if top_confidence < confidence_threshold:
        needs_manual_review = True
        review_reasons.append(
            f"Low confidence score ({top_confidence:.4f} < {confidence_threshold:.2f})"
        )

    # Heuristic B: Sibling Ambiguity Gap (Top 1 vs Top 2)
    # If confidence is below high_confidence_auto_approve (0.65) and gap between #1 and #2 is < 0.01
    if len(fused_candidates) >= 2 and top_confidence < high_confidence_auto_approve:
        gap = top_confidence - fused_candidates[1]['fused_score']
        if gap < ambiguity_gap_threshold:
            needs_manual_review = True
            review_reasons.append(
                f"Ambiguous top candidates (gap between rank 1 and 2 is {gap:.4f} < {ambiguity_gap_threshold:.3f})"
            )

    # Heuristic C: Low Information Flag (Product missing title/description)
    if is_low_info:
        needs_manual_review = True
        review_reasons.append("Low information product record (missing or brief description)")

    # --------------------------------------------------------------------------
    # STEP 7: Category-Specific Attribute Extraction
    # --------------------------------------------------------------------------
    # Extracts allowed taxonomy attributes (Color, Material, Style, etc.) using RapidFuzz
    extracted_attributes = {}
    target_category = top_candidate.get("category") or top_candidate.get("category_id")
    if target_category:
        extracted_attributes = extract_attributes(product, target_category)

    duration_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "predicted_category": top_candidate.get("category"),
        "category_id": top_candidate["category_id"],
        "name": top_candidate["name"],
        "full_name": top_candidate["full_name"],
        "confidence": top_confidence,
        "alternative_categories": alternative_categories,
        "extracted_attributes": extracted_attributes,
        "needs_manual_review": needs_manual_review,
        "review_reasons": review_reasons,
        "used_image": used_image,
        "image_url": image_url if used_image else None,
        "text_predictions": text_preds,
        "image_predictions": [
            {
                "category_id": item[0].get('category_id') if isinstance(item[0], dict) else getattr(item[0], 'id', str(item[0])),
                "name": item[0].get('name') if isinstance(item[0], dict) else getattr(item[0], 'name', ''),
                "score": item[1]
            }
            for item in image_preds_raw
        ],
        "is_low_info": is_low_info,
        "latency_ms": duration_ms,
        "status": "done"
    }
