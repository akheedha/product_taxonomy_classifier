"""
Classification confidence calibration and manual review reasoning logic.
"""

from typing import Dict, Any, List, Tuple, Optional
from common.constants import (
    DEFAULT_CONFIDENCE_THRESHOLD,
    DEFAULT_LOW_CONFIDENCE_THRESHOLD,
    DEFAULT_AMBIGUITY_GAP_THRESHOLD,
    REASON_LOW_CONFIDENCE,
    REASON_AMBIGUOUS_CANDIDATES,
    REASON_LOW_INFORMATION,
    REASON_IMAGE_FETCH_FAILED,
    REASON_DISAGREEMENT,
    MULTIPLIER_FULL_DATA,
    MULTIPLIER_TITLE_IMAGE,
    MULTIPLIER_TITLE_DESC,
    MULTIPLIER_TITLE_ONLY,
    AGREEMENT_BONUS
)


class ConfidenceEvaluator:
    """
    Computes calibrated prediction confidence, evaluates multi-candidate ambiguity gaps,
    applies modality completeness multipliers, and generates human-explainable review reasons.
    """

    @classmethod
    def evaluate(
        cls,
        raw_score: float,
        candidates: List[Dict[str, Any]],
        has_description: bool,
        has_valid_image: bool,
        image_error: bool = False,
        cross_modal_agreement: bool = False,
        threshold: float = DEFAULT_CONFIDENCE_THRESHOLD
    ) -> Dict[str, Any]:
        reasons = []

        # 1. Determine modality multiplier
        if has_description and has_valid_image:
            multiplier = MULTIPLIER_FULL_DATA
        elif has_valid_image and not has_description:
            multiplier = MULTIPLIER_TITLE_IMAGE
            reasons.append(REASON_LOW_INFORMATION)
        elif has_description and not has_valid_image:
            multiplier = MULTIPLIER_TITLE_DESC
        else:
            multiplier = MULTIPLIER_TITLE_ONLY
            reasons.append(REASON_LOW_INFORMATION)

        if image_error:
            reasons.append(REASON_IMAGE_FETCH_FAILED)

        # 2. Base calibrated score calculation
        score = raw_score * multiplier
        if cross_modal_agreement:
            score += AGREEMENT_BONUS

        score = max(0.05, min(0.99, score))

        # 3. Ambiguity gap evaluation (top 1 vs top 2 candidate margin)
        if len(candidates) >= 2:
            top1_score = candidates[0].get('score', 0.0)
            top2_score = candidates[1].get('score', 0.0)
            gap = top1_score - top2_score

            if gap < DEFAULT_AMBIGUITY_GAP_THRESHOLD:
                reasons.append(REASON_AMBIGUOUS_CANDIDATES)
                # Apply margin penalty
                score = max(0.10, score - 0.10)

        # 4. Low confidence evaluation
        if score < DEFAULT_LOW_CONFIDENCE_THRESHOLD:
            reasons.append(REASON_LOW_CONFIDENCE)

        # Determine review flag
        needs_review = (score < threshold) or (len(reasons) > 0)

        return {
            'calibrated_confidence': round(score, 3),
            'needs_manual_review': needs_review,
            'review_reasons': list(dict.fromkeys(reasons)),
            'margin_gap': round(candidates[0].get('score', 0.0) - candidates[1].get('score', 0.0), 3) if len(candidates) >= 2 else 1.0,
        }
