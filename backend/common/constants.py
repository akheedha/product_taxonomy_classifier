"""
System-wide constants and enumerations for the taxonomy classification platform.
"""

# Default thresholds
DEFAULT_CONFIDENCE_THRESHOLD = 0.70
DEFAULT_AMBIGUITY_GAP_THRESHOLD = 0.08
DEFAULT_LOW_CONFIDENCE_THRESHOLD = 0.55
DEFAULT_BATCH_SIZE = 100

# Review reasons
REASON_LOW_CONFIDENCE = "Low confidence (< 0.55)"
REASON_AMBIGUOUS_CANDIDATES = "Ambiguous top candidates (gap < 0.05)"
REASON_LOW_INFORMATION = "Low information (missing/empty description)"
REASON_IMAGE_FETCH_FAILED = "Image fetch failed / inaccessible URL"
REASON_DISAGREEMENT = "Cross-modal signal disagreement"
REASON_MANUAL_FLAG = "Manual curator inspection required"

# Modality weightings
WEIGHT_TEXT = 0.55
WEIGHT_IMAGE = 0.35
WEIGHT_LEXICAL = 0.10

# Multipliers & bonuses
AGREEMENT_BONUS = 0.15
MULTIPLIER_FULL_DATA = 1.00
MULTIPLIER_TITLE_IMAGE = 0.90
MULTIPLIER_TITLE_DESC = 0.85
MULTIPLIER_TITLE_ONLY = 0.70
