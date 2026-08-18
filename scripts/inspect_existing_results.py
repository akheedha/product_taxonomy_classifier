import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxonomy_classifier.settings.dev')
django.setup()

from classification.models import ClassificationResult, ClassificationJob
from collections import Counter

job = ClassificationJob.objects.get(id=4)
results = list(ClassificationResult.objects.filter(job=job, status='done').select_related('product', 'predicted_category'))

print(f"Total Completed Results in Job #{job.id}: {len(results)}")

needs_review_results = [r for r in results if r.needs_manual_review]
print(f"Needs Review: {len(needs_review_results)} / {len(results)} ({len(needs_review_results)/len(results)*100:.1f}%)")

# Inspect reasons by running checks
low_conf_count = 0
ambiguous_gap_count = 0
missing_desc_count = 0
low_info_count = 0
confidences = []
gaps = []

for r in results:
    p = r.product
    conf = r.confidence
    confidences.append(conf)
    
    # Check low confidence (< 0.55)
    if conf < 0.55:
        low_conf_count += 1
        
    # Check ambiguity gap
    alts = r.alternative_categories
    if alts and len(alts) > 0:
        gap = conf - alts[0].get('score', 0)
        gaps.append(gap)
        if gap < 0.05:
            ambiguous_gap_count += 1
            
    # Check missing description / low info
    desc = (p.product_description or '').strip()
    if not desc:
        missing_desc_count += 1
        low_info_count += 1
    elif len(desc) < 30:
        low_info_count += 1

print("\n=== DETAILED HEURISTIC ROOT-CAUSE BREAKDOWN ===")
print(f"1. Low Confidence (< 0.55)                   : {low_conf_count:>4} / {len(results)} ({low_conf_count/len(results)*100:.1f}%)")
print(f"2. Ambiguous Gap (Gap < 0.05 between Top 2)   : {ambiguous_gap_count:>4} / {len(results)} ({ambiguous_gap_count/len(results)*100:.1f}%)")
print(f"3. Missing Description (Empty in Catalog)     : {missing_desc_count:>4} / {len(results)} ({missing_desc_count/len(results)*100:.1f}%)")
print(f"4. Low Information Text Flag                  : {low_info_count:>4} / {len(results)} ({low_info_count/len(results)*100:.1f}%)")

print(f"\nConfidence Stats:")
print(f"  - Min: {min(confidences):.4f}")
print(f"  - Max: {max(confidences):.4f}")
print(f"  - Mean: {sum(confidences)/len(confidences):.4f}")
print(f"  - Median: {sorted(confidences)[len(confidences)//2]:.4f}")

if gaps:
    print(f"\nAmbiguity Gap Stats (Top 1 vs Top 2):")
    print(f"  - Min Gap: {min(gaps):.4f}")
    print(f"  - Max Gap: {max(gaps):.4f}")
    print(f"  - Mean Gap: {sum(gaps)/len(gaps):.4f}")
    print(f"  - Median Gap: {sorted(gaps)[len(gaps)//2]:.4f}")

print("\n=== SAMPLE 5 'NEEDS REVIEW' PRODUCTS WITH METRICS ===")
for r in needs_review_results[:5]:
    p = r.product
    alts = r.alternative_categories
    top2_score = alts[0]['score'] if alts else 0.0
    gap = r.confidence - top2_score
    print(f"\nProduct SKU: {p.product_number}")
    print(f"  Title:            {p.product_name}")
    print(f"  Source Cat:       {p.product_category} > {p.product_sub_category}")
    print(f"  Has Description:  {bool((p.product_description or '').strip())} (length: {len(p.product_description or '')})")
    print(f"  Predicted Cat:    {r.predicted_category.full_name if r.predicted_category else 'None'}")
    print(f"  Top Confidence:   {r.confidence:.4f}")
    if alts:
        print(f"  #2 Alternative:   {alts[0]['full_name']} (score: {top2_score:.4f}, gap: {gap:.4f})")
    print(f"  Triggered Rules:  "
          f"{' [Low Confidence (<0.55)]' if r.confidence < 0.55 else ''}"
          f"{' [Ambiguity Gap (<0.05)]' if gap < 0.05 else ''}"
          f"{' [Missing Description]' if not (p.product_description or '').strip() else ''}"
    )
