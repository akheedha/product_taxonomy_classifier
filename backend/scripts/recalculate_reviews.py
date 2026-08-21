import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from classification.models import ClassificationResult
from classification.engine.fusion import classify_product

results = list(ClassificationResult.objects.filter(status='done'))
print(f"Recalculating review flags for {len(results)} classification results...")

recalculated = 0
changed_flags = 0

for r in results:
    res = classify_product(r.product)
    old_review = r.needs_manual_review
    new_review = res['needs_manual_review']
    
    r.confidence = res['confidence']
    r.needs_manual_review = new_review
    r.save(update_fields=['confidence', 'needs_manual_review'])
    recalculated += 1
    
    if old_review != new_review:
        changed_flags += 1

print(f"Done! Recalculated {recalculated} items. Changed flags for {changed_flags} items.")
