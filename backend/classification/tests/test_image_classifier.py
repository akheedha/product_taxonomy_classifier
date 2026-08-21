from django.test import TestCase
from classification.engine.image_classifier import classify_image


class ImageClassifierTests(TestCase):
    def test_missing_or_invalid_image_url(self):
        # Gracefully handle missing/empty URL
        result = classify_image(image_url=None, candidate_categories=[])
        self.assertEqual(result, [])

    def test_invalid_scheme_url(self):
        result = classify_image(image_url="not_a_valid_url", candidate_categories=[])
        self.assertEqual(result, [])
