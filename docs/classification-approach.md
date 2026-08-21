# Multi-Modal Classification & Confidence Approach

## 1. Multi-Modal Late Fusion Overview

E-commerce products present heterogeneous data signals:
- Some products have rich marketing copy and bullet points.
- Other products have brief, generic titles (e.g. "Accent Chair") with high-resolution imagery.
- Some products have missing images or broken external URLs.

To handle these conditions robustly, our pipeline uses a **Multi-Modal Late Fusion Architecture**:

```
Product Data
 ├── Text Signals (Title, Brand, Category, Materials, Description) ──► Sentence-Transformers (all-MiniLM-L6-v2) ──┐
 │                                                                                                                ├──► Weighted Linear Fusion ──► Confidence Evaluator ──► Result
 └── Visual Signals (Product Image URLs) ──────────────────────────► OpenCLIP ViT-B-32 Zero-Shot Classifier ─────┘
```

---

## 2. Text Semantic Classification
- **Model:** Sentence-Transformers `all-MiniLM-L6-v2` generating 384-dimensional dense semantic embeddings.
- **Taxonomy Pre-indexing:** All 14,606 Shopify category breadcrumb paths (e.g. `Furniture > Chairs > Armchairs & Accent Chairs`) are pre-indexed into a normalized vector matrix.
- **Lexical Re-ranking:** RapidFuzz token-sort similarity is applied to boost exact keyword matches (e.g., matching "sofa" directly against category leaf names).
- **Candidate Generation:** Top 5 candidate categories are generated for visual evaluation.

---

## 3. Visual Zero-Shot Classification
- **Model:** OpenCLIP `ViT-B-32` (trained on LAION-2B).
- **Zero-Shot Prompting:** Evaluates image cosine similarity against candidate category text prompts (e.g., `"a product photo of {category_name}"`).
- **Resilience:** If the image is missing, 404s, or fails to download, the pipeline automatically falls back to text predictions with calibrated confidence.

---

## 4. Late Fusion Formula
For candidate category $c$:
$$\text{Score}(c) = w_{\text{text}} \cdot S_{\text{text}}(c) + w_{\text{image}} \cdot S_{\text{image}}(c)$$

Where default weights are:
- $w_{\text{text}} = 0.60$
- $w_{\text{image}} = 0.40$ (when image is present)

---

## 5. Confidence Calibration & Review Triggers

The `ConfidenceEvaluator` applies explainable heuristics to assign `needs_manual_review = True`:

1. **Modality Availability Multiplier:**
   - Full Data (Text + Image): $1.00\times$
   - Title + Image: $0.90\times$
   - Title + Description (No Image): $0.85\times$
   - Title Only: $0.70\times$ (low information penalty)

2. **Sibling Ambiguity Gap:**
   If the score difference between Rank 1 and Rank 2 predictions is $< 0.01$ (and top score $< 0.65$), the item is flagged for human review due to borderline category ambiguity.

3. **Absolute Confidence Threshold:**
   Predictions with calibrated confidence $< 0.55$ are automatically routed to the Curator Review Queue.
