"""
Sanity check test script for TextCategoryClassifier.
Evaluates category predictions for sample products from database.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import django
# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'taxonomy_classifier.settings.dev')
django.setup()

from catalog.models import Product
from classification.engine.text_classifier import TextCategoryClassifier, classify_text


def run_sanity_check(sample_size: int = 10):
    print("=" * 80)
    print("SHOPIFY TAXONOMY CLASSIFIER - SANITY CHECK")
    print("=" * 80)

    # Initialize classifier (will compute and cache embeddings on first run)
    print("\nInitializing TextCategoryClassifier...")
    classifier = TextCategoryClassifier.get_instance()
    print(f"Categories indexed: {len(classifier.category_metadata):,}")

    # Fetch 10 sample products across different categories
    products = list(Product.objects.all()[:sample_size])
    if not products:
        print("No products found in database! Please run 'python manage.py import_products' first.")
        return

    print(f"\nEvaluating {len(products)} sample products...\n")

    for idx, product in enumerate(products, 1):
        predictions, meta = classifier.classify_text(product, top_k=3)

        low_info_tag = " [LOW INFORMATION]" if meta.get("is_low_info") else ""
        print(f"[{idx}/{len(products)}] Product SKU: {product.product_number}{low_info_tag}")
        print(f"  Title:        {product.product_name}")
        print(f"  Source Cat:   {product.product_category} > {product.product_sub_category or 'N/A'}")
        print(f"  Color/Mat:    {product.product_color or 'N/A'} | {product.materials or 'N/A'}")
        print(f"  Latency:      {meta.get('latency_ms', 0):.1f} ms")
        print("  Top Predicted Shopify Taxonomy Categories:")

        for rank, pred in enumerate(predictions, 1):
            score_bar = "#" * int(pred['score'] * 20)
            print(
                f"    {rank}. [{pred['score']:.4f}] {pred['name']} (Level {pred['level']})"
            )
            print(f"       Path: {pred['full_name']}")

        print("-" * 80)

    # Test edge case: Product with missing description
    print("\n--- Edge Case Test: Product with Missing Description ---")
    mock_sparse_product = Product(
        product_number="SPARSE-001",
        product_name="Solid Teak Outdoor Dining Table",
        product_category="Outdoor",
        product_sub_category="Dining Tables",
        product_description="",
        materials="Teak Wood"
    )
    sparse_preds, sparse_meta = classifier.classify_text(mock_sparse_product, top_k=3)
    print(f"Sparse Product: {mock_sparse_product.product_name}")
    print(f"Is Low Info: {sparse_meta.get('is_low_info')}")
    print("Top Predictions:")
    for rank, pred in enumerate(sparse_preds, 1):
        print(f"  {rank}. [{pred['score']:.4f}] {pred['full_name']}")

    print("\n" + "=" * 80)
    print("Sanity check completed successfully!")
    print("=" * 80)


if __name__ == '__main__':
    run_sanity_check(10)
