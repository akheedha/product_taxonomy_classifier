"""
End-to-end sanity check script for Multimodal Fusion & Attribute Extraction Pipeline.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from products.models import Product
from classification.engine.fusion import classify_product


def run_pipeline_check(sample_size: int = 5):
    print("=" * 80)
    print("MULTIMODAL TAXONOMY CLASSIFICATION & ATTRIBUTE EXTRACTION PIPELINE")
    print("=" * 80)

    products = list(Product.objects.all()[:sample_size])
    if not products:
        print("No products in database.")
        return

    for idx, product in enumerate(products, 1):
        result = classify_product(product)

        print(f"\n[{idx}/{len(products)}] Product SKU: {product.product_number}")
        print(f"  Title:            {product.product_name}")
        print(f"  Source Cat:       {product.product_category} > {product.product_sub_category}")
        print(f"  Color / Material: {product.product_color} | {product.materials}")
        print(f"  Image Attached:   {'Yes (' + result['image_url'][:40] + '...)' if result['used_image'] else 'No / Skipped'}")
        print(f"  Predicted Cat:    {result['full_name']}")
        print(f"  Confidence:       {result['confidence']:.4f} ({result['confidence']*100:.1f}%)")
        print(f"  Manual Review:    {result['needs_manual_review']} ({', '.join(result['review_reasons']) if result['review_reasons'] else 'High Confidence'})")

        print("  Extracted Attributes:")
        if result['extracted_attributes']:
            for attr_name, attr_data in result['extracted_attributes'].items():
                print(f"    - {attr_name}: '{attr_data['value']}' (confidence: {attr_data['confidence']:.2f})")
        else:
            print("    (None matched above threshold)")

        print("  Alternatives:")
        for alt in result['alternative_categories']:
            print(f"    * [{alt['score']:.4f}] {alt['full_name']}")

        print("-" * 80)


if __name__ == '__main__':
    run_pipeline_check(5)
