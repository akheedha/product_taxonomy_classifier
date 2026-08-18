"""
================================================================================
ZERO-SHOT IMAGE CLASSIFIER (OPENCLIP VISION-LANGUAGE ENGINE)
================================================================================
Purpose:
  Provides visual zero-shot classification for e-commerce products by analyzing product
  photographs (URLs) and comparing visual representations against candidate categories.

Core Technology:
  - Architecture: OpenCLIP ViT-B/32 (Vision Transformer Base, 32x32 patch size)
  - Pretrained Weights: 'openai'
  - Shared Embedding Space: Aligns 512-dimensional visual features with textual prompts.
  - Fault Tolerance: Resilient image fetching with retries, timeout bounds, and graceful
    fallback to text-only classification if the image is missing or unreachable.
"""

import io
import logging
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import open_clip
import requests
import torch
from PIL import Image
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

# Model Architecture Configuration
CLIP_MODEL_NAME = 'ViT-B-32'
CLIP_PRETRAINED = 'openai'

# Global model state cache (loaded once in RAM across Celery workers)
_MODEL = None
_PREPROCESS = None
_TOKENIZER = None
_DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'


def get_clip_resources() -> Tuple[torch.nn.Module, Any, Any, str]:
    """
    Lazy loads and caches the OpenCLIP ViT-B-32 model, TorchVision preprocessing transforms,
    and text tokenizer on GPU/CPU.
    """
    global _MODEL, _PREPROCESS, _TOKENIZER, _DEVICE
    if _MODEL is None:
        logger.info(f"Loading OpenCLIP '{CLIP_MODEL_NAME}' (pretrained: {CLIP_PRETRAINED}) on {_DEVICE}...")
        _MODEL, _, _PREPROCESS = open_clip.create_model_and_transforms(
            CLIP_MODEL_NAME,
            pretrained=CLIP_PRETRAINED
        )
        _MODEL = _MODEL.to(_DEVICE)
        _MODEL.eval()  # Set to inference evaluation mode
        _TOKENIZER = open_clip.get_tokenizer(CLIP_MODEL_NAME)
    return _MODEL, _PREPROCESS, _TOKENIZER, _DEVICE


def download_image(
    image_url: str,
    timeout: Tuple[float, float] = (3.0, 6.0),
    max_retries: int = 2
) -> Optional[Image.Image]:
    """
    Safely downloads a remote image over HTTP/HTTPS with retries, custom headers, and timeouts.

    Args:
        image_url: Direct web URL to the product image.
        timeout: Tuple of (connect_timeout_seconds, read_timeout_seconds).
        max_retries: Number of connection retry attempts on transient network errors.

    Returns:
        PIL.Image in RGB mode if successful, or None if download fails.
    """
    if not image_url or not isinstance(image_url, str):
        return None

    url = image_url.strip()
    if not url.startswith(('http://', 'https://')):
        return None

    # Configure resilient HTTP session with retry adapter
    session = requests.Session()
    retries = Retry(
        total=max_retries,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
        raise_on_status=False
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('http://', adapter)
    session.mount('https://', adapter)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) TaxonomyClassifier/1.0',
        'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
    }

    try:
        response = session.get(url, headers=headers, timeout=timeout)
        if response.status_code != 200:
            logger.warning(f"Failed to fetch image HTTP {response.status_code} from {url}")
            return None

        # Convert image stream to PIL RGB image
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
        return image
    except Exception as e:
        logger.warning(f"Error downloading image from {url}: {e}")
        return None
    finally:
        session.close()


def _format_candidate_prompt(candidate: Any) -> str:
    """
    Synthesizes natural language text prompt for CLIP zero-shot matching.
    Example: 'Furniture > Sofas > Sectional Sofas' -> 'a product photo of Sectional Sofas, category Furniture'
    """
    name = ""
    full_name = ""

    if isinstance(candidate, dict):
        name = candidate.get('name', '')
        full_name = candidate.get('full_name', '')
    elif hasattr(candidate, 'name'):
        name = getattr(candidate, 'name', '')
        full_name = getattr(candidate, 'full_name', '')
    elif isinstance(candidate, str):
        name = candidate

    if full_name and '>' in full_name:
        parts = [p.strip() for p in full_name.split('>')]
        return f"a product photo of {parts[-1]}, category {parts[0]}"
    elif name:
        return f"a product photo of {name}"
    return "a product photo"


def classify_image(
    image_url: str,
    candidate_categories: List[Any],
    product_id: Optional[str] = None
) -> List[Tuple[Any, float]]:
    """
    Zero-shot visual scoring of an image against candidate taxonomy categories using CLIP.

    Workflow:
      1. Downloads image asynchronously with safety timeouts.
      2. Preprocesses image into standard ViT-B-32 tensor (224x224 normalized).
      3. Passes synthesized category text prompts through CLIP text encoder.
      4. Computes matrix dot product of normalized image and text embeddings.
      5. Rescales similarity scores into calibrated [0.0, 1.0] confidence range.

    Args:
        image_url: Direct URL string to product image.
        candidate_categories: Top candidate categories generated by text stage.
        product_id: Optional product SKU for logging context.

    Returns:
        List of tuples: (candidate_category, visual_score) sorted by score descending.
    """
    if not image_url or not candidate_categories:
        return []

    pid_str = f" for product [{product_id}]" if product_id else ""

    try:
        # Step 1: Download image
        pil_image = download_image(image_url)
        if pil_image is None:
            logger.warning(f"Image download failed{pid_str} (URL: {image_url})")
            return []

        # Step 2: Get cached CLIP models
        model, preprocess, tokenizer, device = get_clip_resources()

        # Step 3: Transform image to PyTorch tensor
        image_tensor = preprocess(pil_image).unsqueeze(0).to(device)

        # Step 4: Tokenize candidate category prompts
        prompts = [_format_candidate_prompt(cat) for cat in candidate_categories]
        text_tokens = tokenizer(prompts).to(device)

        with torch.no_grad():
            # Extract 512-d feature vectors
            image_features = model.encode_image(image_tensor)
            text_features = model.encode_text(text_tokens)

            # L2 Normalize feature vectors
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

            # Compute raw cosine similarity (range ~0.10 to ~0.35)
            similarity = (image_features @ text_features.T).squeeze(0)

            # Rescale typical CLIP similarity range (0.10 - 0.35) into standard [0.0, 1.0] confidence
            sim_scores = similarity.cpu().numpy()
            min_expected, max_expected = 0.10, 0.35
            norm_scores = np.clip((sim_scores - min_expected) / (max_expected - min_expected), 0.0, 1.0)

        # Step 5: Pair candidates with scores and sort descending
        scored_candidates = []
        for cat, score in zip(candidate_categories, norm_scores):
            scored_candidates.append((cat, round(float(score), 4)))

        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        return scored_candidates

    except Exception as e:
        logger.warning(f"Zero-shot image classification error{pid_str} on {image_url}: {e}")
        return []
