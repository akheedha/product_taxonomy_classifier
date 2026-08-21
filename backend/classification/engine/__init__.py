"""
Classification engine package containing text, image, attribute extraction, and multimodal fusion classifiers.
"""
from .text_classifier import TextCategoryClassifier, classify_text
from .image_classifier import classify_image, download_image
from .attribute_extractor import extract_attributes
from .fusion import (
    classify_product,
    TEXT_WEIGHT,
    IMAGE_WEIGHT,
    CONFIDENCE_THRESHOLD,
    AMBIGUITY_GAP_THRESHOLD,
)

__all__ = [
    'TextCategoryClassifier',
    'classify_text',
    'classify_image',
    'download_image',
    'extract_attributes',
    'classify_product',
    'TEXT_WEIGHT',
    'IMAGE_WEIGHT',
    'CONFIDENCE_THRESHOLD',
    'AMBIGUITY_GAP_THRESHOLD',
]
