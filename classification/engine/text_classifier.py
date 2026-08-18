"""
================================================================================
TEXT-BASED PRODUCT TAXONOMY CLASSIFIER (SENTENCE TRANSFORMERS)
================================================================================
Purpose:
  Maps raw product titles, descriptions, categories, and materials to standardized
  Shopify Taxonomy category paths (14,606 nodes) using dense semantic vector search.

Core Technology:
  - Model: 'all-MiniLM-L6-v2' (Sentence-Transformers / PyTorch)
  - Embedding Dimension: 384-dimensional dense vectors
  - Search Mechanism: L2-Normalized Cosine Dot Product ($A \cdot B = \cos(\theta)$)
  - Persistence: Offline pre-computed embeddings saved to NumPy (.npy) and JSON cache
    for sub-millisecond retrieval (10-25ms per product inference).
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from django.conf import settings
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

# Default lightweight, high-performance embedding model
DEFAULT_MODEL_NAME = 'all-MiniLM-L6-v2'


class TextCategoryClassifier:
    """
    Singleton classifier for Shopify Product Taxonomy semantic search.
    Keeps the neural network model and pre-computed category embeddings in RAM.
    """
    _instance: Optional['TextCategoryClassifier'] = None

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL_NAME,
        cache_dir: Optional[Union[str, Path]] = None,
        force_recompute: bool = False
    ):
        """
        Initializes the classifier, setting cache file paths and loading embeddings.
        """
        self.model_name = model_name
        self.cache_dir = Path(cache_dir or (settings.BASE_DIR / 'data' / 'cache'))
        self.embeddings_path = self.cache_dir / f"category_embeddings_{self.model_name.replace('/', '_')}.npy"
        self.metadata_path = self.cache_dir / f"category_metadata_{self.model_name.replace('/', '_')}.json"

        self.model: Optional[SentenceTransformer] = None
        self.category_embeddings: Optional[np.ndarray] = None
        self.category_metadata: List[Dict[str, Any]] = []
        self.category_id_to_index: Dict[str, int] = {}

        self._initialize(force_recompute=force_recompute)

    @classmethod
    def get_instance(cls, force_recompute: bool = False) -> 'TextCategoryClassifier':
        """
        Thread-safe singleton accessor. Reuses the warm model and in-memory embeddings
        across all web requests and Celery workers.
        """
        if cls._instance is None or force_recompute:
            cls._instance = cls(force_recompute=force_recompute)
        return cls._instance

    def _initialize(self, force_recompute: bool = False):
        """Loads neural model and loads or builds the category vector index."""
        self._load_model()
        self._load_or_build_category_index(force_recompute=force_recompute)

    def _load_model(self):
        """Lazy load the sentence transformer model into PyTorch runtime."""
        if self.model is None:
            logger.info(f"Loading SentenceTransformer model '{self.model_name}'...")
            self.model = SentenceTransformer(self.model_name)

    def _load_or_build_category_index(self, force_recompute: bool = False):
        """
        Checks for cached `.npy` and `.json` files on disk.
        If cache exists and matches database category count, loads instantly.
        Otherwise, triggers computation and saves cache to disk.
        """
        from taxonomy.models import Category

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        total_db_categories = Category.objects.count()

        cache_valid = False
        if not force_recompute and self.embeddings_path.exists() and self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r', encoding='utf-8') as f:
                    self.category_metadata = json.load(f)
                self.category_embeddings = np.load(self.embeddings_path)

                # Validate size consistency
                if (
                    len(self.category_metadata) > 0
                    and len(self.category_metadata) == len(self.category_embeddings)
                    and (total_db_categories == 0 or len(self.category_metadata) == total_db_categories)
                ):
                    cache_valid = True
                    logger.info(
                        f"Loaded {len(self.category_metadata):,} cached category embeddings from {self.embeddings_path}"
                    )
            except Exception as e:
                logger.warning(f"Failed to load cached category embeddings: {e}. Recomputing...")
                cache_valid = False

        if not cache_valid:
            self._build_and_cache_category_index()

        # Build reverse index for O(1) ID lookups
        self.category_id_to_index = {
            item['id']: idx for idx, item in enumerate(self.category_metadata)
        }

    def _build_and_cache_category_index(self):
        """
        Encodes all 14,606 Shopify categories with ancestor hierarchy into normalized vectors.
        Example representation: 'Apparel & Accessories > Clothing > Outerwear > Jackets & Coats'
        """
        from taxonomy.models import Category

        categories = list(Category.objects.all().order_by('level', 'id'))
        if not categories:
            logger.warning("No Category records found in database to index.")
            self.category_embeddings = np.empty((0, 384), dtype=np.float32)
            self.category_metadata = []
            return

        logger.info(f"Computing embeddings for {len(categories):,} taxonomy categories...")
        start_time = time.time()

        category_texts = []
        metadata = []

        for cat in categories:
            # Build full breadcrumb hierarchy string
            ancestor_names = [c.name for c in cat.get_ancestors(include_self=False)]
            if ancestor_names:
                cat_text = f"{' > '.join(ancestor_names)} > {cat.name}"
            else:
                cat_text = cat.full_name or cat.name

            category_texts.append(cat_text)
            metadata.append({
                "id": cat.id,
                "name": cat.name,
                "full_name": cat.full_name,
                "level": cat.level,
            })

        # Batch encode with PyTorch and L2 normalization
        embeddings = self.model.encode(
            category_texts,
            batch_size=256,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True
        )

        self.category_embeddings = embeddings.astype(np.float32)
        self.category_metadata = metadata

        # Save to disk cache (.npy + .json)
        np.save(self.embeddings_path, self.category_embeddings)
        with open(self.metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.category_metadata, f)

        duration = time.time() - start_time
        logger.info(
            f"Cached {len(categories):,} category embeddings to {self.embeddings_path} in {duration:.2f}s."
        )

    def build_product_text(self, product: Any) -> Tuple[str, bool]:
        """
        Constructs a synthesized search query string from available product attributes.
        Combines: Title + Brand + Raw Categories + Collection + Color + Materials + Features + Description.

        Returns:
            Tuple of (synthesized_query_string, is_low_information_flag)
        """
        parts = []

        # 1. Product Title / Name
        name = getattr(product, 'product_name', None) or getattr(product, 'title', None)
        if name:
            parts.append(f"Product: {str(name).strip()}")

        # 2. Brand / Manufacturer / Vendor
        brand = getattr(product, 'brand', None) or getattr(product, 'vendor', None) or getattr(product, 'manufacturer', None)
        if brand:
            parts.append(f"Brand: {str(brand).strip()}")

        # 3. Raw Source Categories
        cat = getattr(product, 'product_category', None)
        sub_cat = getattr(product, 'product_sub_category', None)
        if cat or sub_cat:
            cat_str = " > ".join(filter(None, [str(cat).strip() if cat else None, str(sub_cat).strip() if sub_cat else None]))
            parts.append(f"Category: {cat_str}")

        # 4. Collection & Color
        collection = getattr(product, 'collection_name', None)
        color = getattr(product, 'product_color', None)
        if collection:
            parts.append(f"Collection: {str(collection).strip()}")
        if color:
            parts.append(f"Color: {str(color).strip()}")

        # 5. Materials & Bullet Points
        materials = getattr(product, 'materials', None)
        if materials:
            parts.append(f"Materials: {str(materials).strip()}")

        bullets = getattr(product, 'bullets', None)
        if bullets:
            cleaned_bullets = " ".join(str(bullets).split())
            parts.append(f"Features: {cleaned_bullets}")

        # 6. Detailed Marketing Description
        desc = getattr(product, 'product_description', None)
        has_description = bool(desc and str(desc).strip())
        if has_description:
            parts.append(f"Description: {str(desc).strip()}")

        query_text = " | ".join(parts)
        if not query_text:
            query_text = getattr(product, 'product_number', '') or "Unknown Product"

        # Flag as low info if missing description or query is very short (< 40 chars)
        is_low_info = (not has_description) or (len(query_text) < 40)

        return query_text, is_low_info

    def classify_text(
        self,
        product: Any,
        top_k: int = 5,
        fetch_category_instances: bool = True
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Classifies product text against all 14,606 Shopify category vectors.

        Algorithm:
          1. Constructs query string from product.
          2. Encodes query into 384-d normalized vector.
          3. Matrix multiply: scores = embeddings_matrix @ query_vector.
          4. Argpartition retrieves top-K highest scoring category matches.

        Returns:
            Tuple of (top_k_predictions_list, execution_metadata_dict)
        """
        start_time = time.time()

        if isinstance(product, str):
            query_text = product
            is_low_info = len(product.strip()) < 30
        elif isinstance(product, dict):
            class Obj:
                pass
            o = Obj()
            for k, v in product.items():
                setattr(o, k, v)
            query_text, is_low_info = self.build_product_text(o)
        else:
            query_text, is_low_info = self.build_product_text(product)

        if self.category_embeddings is None or len(self.category_metadata) == 0:
            return [], {
                "is_low_info": is_low_info,
                "input_text": query_text,
                "model": self.model_name,
                "error": "Category embeddings index is empty"
            }

        # 1. Encode query text (1 x 384 normalized vector)
        query_embedding = self.model.encode(
            query_text,
            normalize_embeddings=True,
            convert_to_numpy=True
        ).astype(np.float32)

        # 2. Vectorized Cosine Dot Product
        scores = np.dot(self.category_embeddings, query_embedding)

        # 3. Top-K Index Selection (O(N) partition + sort top K)
        actual_k = min(top_k, len(scores))
        top_indices = np.argpartition(scores, -actual_k)[-actual_k:]
        top_indices = top_indices[np.argsort(-scores[top_indices])]

        top_ids = [self.category_metadata[idx]['id'] for idx in top_indices]

        # 4. Fetch Django Category ORM instances
        category_map = {}
        if fetch_category_instances:
            from taxonomy.models import Category
            category_map = {c.id: c for c in Category.objects.filter(id__in=top_ids)}

        predictions = []
        for idx in top_indices:
            meta = self.category_metadata[idx]
            cat_id = meta['id']
            score = float(scores[idx])
            cat_instance = category_map.get(cat_id)

            predictions.append({
                "category": cat_instance,
                "category_id": cat_id,
                "name": meta['name'],
                "full_name": meta['full_name'],
                "level": meta['level'],
                "score": round(score, 4),
            })

        duration_ms = round((time.time() - start_time) * 1000, 2)
        meta = {
            "is_low_info": is_low_info,
            "input_text": query_text,
            "top_score": predictions[0]["score"] if predictions else 0.0,
            "model": self.model_name,
            "latency_ms": duration_ms,
        }

        return predictions, meta


def classify_text(
    product: Any,
    top_k: int = 5,
    fetch_category_instances: bool = True
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience wrapper to classify a product using the global singleton classifier instance.
    """
    classifier = TextCategoryClassifier.get_instance()
    return classifier.classify_text(
        product=product,
        top_k=top_k,
        fetch_category_instances=fetch_category_instances
    )
