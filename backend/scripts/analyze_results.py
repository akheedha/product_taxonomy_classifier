import os
import sys
from pathlib import Path
from collections import Counter

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from classification.models import ClassificationResult
from classification.engine.fusion import classify_product

results = list(ClassificationResult.objects.filter(status='done')[:100])
print(f"Total results sampled: {len(results)}")

reasons_counter = Counter()
confidences = []
gaps = []
low_info_count = 0
sample_details = []

for idx, r in enumerate(results):
    res = classify_product(r.product)
    conf = res['confidence']
    confidences.append(conf)
    if res['is_low_info']:
        low_info_count += 1

    for reason in res['review_reasons']:
        if 'Low confidence' in reason:
            reasons_counter['Low confidence (< 0.55)'] += 1
        elif 'Ambiguous' in reason:
            reasons_counter['Ambiguous top candidates (gap < 0.05)'] += 1
        elif 'Low information' in reason:
            reasons_counter['Low information (missing/empty description)'] += 1
        else:
            reasons_counter[reason] += 1

    if idx < 10:
        sample_details.append({
            'sku': r.product.product_number,
            'name': r.product.product_name,
            'has_desc': bool(r.product.product_description),
            'desc_len': len(r.product.product_description or ''),
            'conf': round(conf, 3),
            'needs_review': res['needs_manual_review'],
            'reasons': res['review_reasons'],
            'top_cat': res['full_name'],
            'alt_cats': [a['full_name'] for a in res['alternative_categories'][:2]],
        })

print("\n=== REVIEW TRIGGER BREAKDOWN (100 Sample Products) ===")
for reason, count in reasons_counter.most_common():
    print(f"  - {reason:<45}: {count:>3} / {len(results)} ({count/len(results)*100:.1f}%)")

if confidences:
    print(f"\nAverage Confidence Score: {sum(confidences)/len(confidences):.4f}")
    print(f"Min Confidence: {min(confidences):.4f} | Max Confidence: {max(confidences):.4f}")
    print(f"Products with Missing Description: {low_info_count} / {len(results)}")
