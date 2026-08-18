import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxonomy_classifier.settings.dev')
django.setup()

from classification.models import ClassificationResult, ClassificationJob
from classification.engine.fusion import (
    CONFIDENCE_THRESHOLD,
    AMBIGUITY_GAP_THRESHOLD,
    HIGH_CONFIDENCE_AUTO_APPROVE
)

job = ClassificationJob.objects.order_by('-created_at').first()
if not job:
    print("No jobs found.")
    sys.exit(0)

results = list(ClassificationResult.objects.filter(job=job, status='done').select_related('product', 'predicted_category'))
print(f"Recalculating review flags for Job #{job.id} ({len(results)} items)...")
print(f"New Settings: Ambiguity Gap Threshold = {AMBIGUITY_GAP_THRESHOLD}, High-Conf Auto-Approve = {HIGH_CONFIDENCE_AUTO_APPROVE}")

updated_count = 0
new_needs_review_count = 0
auto_approved_count = 0

for r in results:
    p = r.product
    conf = r.confidence
    alts = r.alternative_categories
    desc = (p.product_description or '').strip()
    is_low_info = (not desc) or (len(desc) < 30)
    
    needs_review = False
    
    # 1. Low confidence
    if conf < CONFIDENCE_THRESHOLD:
        needs_review = True
    
    # 2. Ambiguity gap (if confidence < HIGH_CONFIDENCE_AUTO_APPROVE)
    if not needs_review and conf < HIGH_CONFIDENCE_AUTO_APPROVE and alts and len(alts) > 0:
        gap = conf - alts[0].get('score', 0)
        if gap < AMBIGUITY_GAP_THRESHOLD:
            needs_review = True
            
    # 3. Low info
    if not needs_review and is_low_info:
        needs_review = True
        
    if needs_review != r.needs_manual_review:
        r.needs_manual_review = needs_review
        r.save(update_fields=['needs_manual_review'])
        updated_count += 1
        
    if needs_review:
        new_needs_review_count += 1
    else:
        auto_approved_count += 1

print("\n=== RECALCULATION COMPLETE ===")
print(f"  - Total Products:           {len(results)}")
print(f"  - Auto-Approved (Clean):    {auto_approved_count} ({auto_approved_count/len(results)*100:.1f}%)")
print(f"  - Needing Review (Flagged): {new_needs_review_count} ({new_needs_review_count/len(results)*100:.1f}%)")
print(f"  - Rows Updated:             {updated_count}")
