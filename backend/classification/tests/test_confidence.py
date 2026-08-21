from django.test import TestCase
from classification.confidence import ConfidenceEvaluator
from common.constants import (
    REASON_LOW_CONFIDENCE,
    REASON_AMBIGUOUS_CANDIDATES,
    REASON_LOW_INFORMATION
)


class ConfidenceEvaluatorTests(TestCase):
    def test_full_data_high_confidence(self):
        candidates = [
            {'category_id': '1', 'name': 'Sofas', 'score': 0.85},
            {'category_id': '2', 'name': 'Chairs', 'score': 0.50},
        ]
        eval_result = ConfidenceEvaluator.evaluate(
            raw_score=0.85,
            candidates=candidates,
            has_description=True,
            has_valid_image=True
        )
        self.assertFalse(eval_result['needs_manual_review'])
        self.assertGreaterEqual(eval_result['calibrated_confidence'], 0.70)
        self.assertEqual(len(eval_result['review_reasons']), 0)

    def test_low_information_penalty(self):
        candidates = [{'category_id': '1', 'name': 'Sofas', 'score': 0.70}]
        eval_result = ConfidenceEvaluator.evaluate(
            raw_score=0.70,
            candidates=candidates,
            has_description=False,
            has_valid_image=False
        )
        self.assertTrue(eval_result['needs_manual_review'])
        self.assertIn(REASON_LOW_INFORMATION, eval_result['review_reasons'])

    def test_ambiguous_candidates_margin(self):
        candidates = [
            {'category_id': '1', 'name': 'Dining Chairs', 'score': 0.61},
            {'category_id': '2', 'name': 'Office Chairs', 'score': 0.60},
        ]
        eval_result = ConfidenceEvaluator.evaluate(
            raw_score=0.61,
            candidates=candidates,
            has_description=True,
            has_valid_image=True
        )
        self.assertTrue(eval_result['needs_manual_review'])
        self.assertIn(REASON_AMBIGUOUS_CANDIDATES, eval_result['review_reasons'])
