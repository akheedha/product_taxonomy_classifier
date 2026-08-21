# Shopify Product Taxonomy Classifier — Technical Design & Architecture Q&A

This document provides detailed, technically grounded answers to the core architectural and system design requirements of the Shopify Product Taxonomy Classifier & Review Platform.

---

## 1. Automatic Shopify Category, Attribute, and Attribute-Value Identification

### How It Works:
The classification pipeline executes in a multi-stage architecture:
1. **Semantic Text Matching (`classification/engine/text_classifier.py`):**
   - Synthesizes product metadata (`product_name`, `brand`, `product_category`, `materials`, `description`).
   - Generates a dense 384-dimensional semantic embedding via `SentenceTransformers` (`all-MiniLM-L6-v2`).
   - Computes cosine similarity against a pre-indexed vector matrix of all 14,606 Shopify taxonomy breadcrumb paths.
   - Refines rankings with lexical string distance (`RapidFuzz`) to prioritize exact keyword matches.
2. **Category-Specific Attribute Extraction (`classification/engine/attribute_extractor.py`):**
   - When a category is predicted (e.g. `Home & Garden > Furniture > Sofas`), the system queries all valid `Attribute` definitions mapped to this category and its parent ancestors in MariaDB.
   - For each attribute (e.g. `Color`, `Material`, `Style`), the extractor searches field-specific hints (`product_color`, `materials`) and general description text.
   - Matches values against Shopify canonical allowed values using exact word-boundary regex (`\b{val}\b`) and `RapidFuzz` fuzzy partial ratio matching (threshold: 80%).
   - Extracted attributes are stored as structured JSON: `{"Material": {"value": "Teak Wood", "confidence": 0.95}}`.

---

## 2. Handling a Product With Only a Title

### How It Works:
When descriptions, brand, or attributes are missing:
1. **Fallback Text Pipeline:** The text classifier constructs the embedding query solely from `product_name`.
2. **Low-Information Flagging (`is_low_info`):** The system detects that description is empty or under 20 characters and flags the product record.
3. **Confidence Penalty:** In `classification/confidence.py`, a modality penalty ($0.70\times$ multiplier) is applied because rich context is unavailable.
4. **Curator Review Routing:** Because the title lacks corroborating description or image data, the product is automatically assigned `needs_manual_review = True` with the review reason `"Low information product record (missing or brief description)"`.
5. **Alternative Category Candidates:** The top 3 alternative taxonomy categories are persisted alongside the prediction so curators can easily verify or reassign with 1 click in the UI.

---

## 3. Using Product Images to Improve Classification

### How It Works:
1. **Zero-Shot Visual Classification (`classification/engine/image_classifier.py`):**
   - Uses OpenCLIP `ViT-B-32` (trained on LAION-2B) to embed product images into a 512-dimensional shared vision-language space.
   - The top candidate categories from the text stage are converted to natural prompts (e.g. `"a product photo of Sectional Sofas, category Furniture"`).
   - Computes cosine similarity between image embeddings and candidate text prompts.
2. **Late Fusion (`classification/engine/fusion.py`):**
   - Combines normalized text score ($S_{\text{text}}$) and visual score ($S_{\text{image}}$) using a weighted linear combination:
     $$\text{Score}_{\text{fused}} = 0.60 \cdot S_{\text{text}} + 0.40 \cdot S_{\text{image}}$$
   - If an image clearly distinguishes between visually distinct categories (e.g. Desk Chair vs. Dining Chair), the visual signal boosts the correct category.

---

## 4. Efficient Processing of 10,000+ Products

### How It Works:
1. **Asynchronous Background Celery Workers (`processing/tasks.py`):**
   - Long-running classification batches are decoupled from synchronous HTTP request/response lifecycles.
   - The frontend initiates a job via `POST /api/jobs/` and immediately receives a `job_id` for background polling.
2. **Chunked Stream Processing (`processing/batch_processor.py`):**
   - Products are read and processed in controlled chunks of 100 items to prevent RAM exhaustion.
3. **Database Checkpoints:**
   - Progress counters are committed periodically (every 5 items) to MariaDB.
4. **Pre-indexed Embedding Matrix:**
   - Taxonomy category embeddings are computed once and cached in RAM, eliminating repeated inference over 14.6k categories per product.

---

## 5. Storing Shopify Taxonomy and Category Hierarchy

### How It Works:
The taxonomy schema is stored in relational MariaDB tables (`taxonomy/models.py`):
1. **`taxonomy_categories` Table:**
   - Fields: `id` (GID string, e.g. `gid://shopify/TaxonomyCategory/aa-1`), `name`, `full_name` (breadcrumb path), `parent_id` (foreign key to self), `level` (1 for L1, 2 for L2, etc.), `is_leaf` (boolean).
   - Indexed on `full_name`, `name`, and `parent_id` for fast sub-tree queries.
2. **`taxonomy_attributes` & `taxonomy_attribute_values` Tables:**
   - Many-to-many relationships link allowed attributes and standardized value sets to specific categories and their inheritance chains.
3. **Hierarchy Traversal:**
   - The `Category` model provides `get_ancestors()` and `get_children()` helper methods to traverse up and down the taxonomy tree efficiently.

---

## 6. Determining Classification Confidence

### How It Works:
Confidence is calculated mathematically in `classification/confidence.py` using calibrated signals:
1. **Base Score:** Fused similarity score from text and vision embeddings ($0.0$ to $1.0$).
2. **Modality Multiplier:** Multiplied by signal completeness factor ($1.00\times$ for text+image, $0.90\times$ for title+image, $0.85\times$ for text only, $0.70\times$ for title only).
3. **Decisive Thresholds:**
   - **High Confidence ($\ge 0.65$):** Auto-approved without review requirement.
   - **Medium Confidence ($0.55 \le \text{Score} < 0.65$):** Accepted unless sibling ambiguity gap is narrow.
   - **Low Confidence ($< 0.55$):** Automatically flagged with `needs_manual_review = True`.

---

## 7. Handling Uncertain or Multiple Category Results

### How It Works:
1. **Sibling Ambiguity Detection:**
   - If the difference between the Rank 1 and Rank 2 category score is $< 0.01$ (with score $< 0.65$), the system identifies the prediction as borderline ambiguous.
2. **Persisted Alternatives:**
   - The top 3 alternative category suggestions (`category_id`, `name`, `full_name`, `score`) are stored in `ClassificationResult.alternative_categories` JSON field.
3. **Curator Override Workflow:**
   - In the React Review Queue UI, curators can expand the product drawer, inspect the top alternative categories, or search any canonical taxonomy node with live autocomplete to reassign and approve with one click via `PATCH /api/results/{id}/`.

---

## 8. Handling Broken or Inaccessible Images

### How It Works:
1. **Resilient Downloader (`classification/engine/image_classifier.py`):**
   - Connect and read timeouts bounded at 3.0s / 6.0s with urllib3 retry adapters.
2. **Graceful Fallback:**
   - If an image URL returns HTTP 404, times out, or fails image decoding, the exception is logged as a warning.
   - The product automatically falls back to text-only semantic classification.
3. **Per-Item Isolation:**
   - The batch processor catches any unexpected item-level exceptions, records `status='failed'` for that SKU, and proceeds immediately to the next product without crashing the batch.

---

## 9. API and Database Design

### How It Works:
1. **Database Schema (`products`, `taxonomy`, `classification`, `processing`):**
   - Clean relational models with proper foreign keys, constraints, and database indexes.
   - Products store SKU, titles, descriptions, pricing, and multi-image arrays.
   - Classification results store predicted category FK, confidence float, review flags, extracted attributes JSON, and curator audit timestamps.
2. **REST API Architecture:**
   - Modular DRF ViewSets/APIViews adhering to REST conventions:
     - `/api/products/` — Catalog querying and filtering.
     - `/api/imports/upload/` — Spreadsheet ingestion and quality audit.
     - `/api/taxonomy/categories/` — Taxonomy tree search and hierarchy.
     - `/api/results/` & `/api/results/summary/` — Review table, KPI metrics, and approvals.
     - `/api/jobs/` — Asynchronous batch queue and live progress monitoring.

---

## 10. Optimizing Large Numbers of External AI/API Requests

### How It Works:
1. **Local Pre-Trained Vector Embeddings:**
   - Sentence-Transformers and OpenCLIP run locally in-process with PyTorch, eliminating third-party per-request rate limits and external latency.
2. **Vector Matrix Pre-Indexing:**
   - All 14,606 taxonomy categories are embedded once at startup and stored in RAM. Product classification is reduced to an ultra-fast matrix multiplication ($O(N \cdot D)$ cosine dot product taking $<15\text{ms}$).
3. **Candidate Limiting for Vision:**
   - OpenCLIP zero-shot inference is only evaluated against the top 5 candidate categories produced by the fast text stage, reducing visual text prompt comparisons by $>99.9\%$.

---

## 11. Resuming Processing After Interruption

### How It Works:
1. **State Persistence (`processing/batch_processor.py`):**
   - Every product's outcome is committed upon completion with `status='done'`.
2. **Resumption Query:**
   - When a job is resumed (via `POST /api/jobs/{id}/resume/` or CLI `--resume`), the processor queries existing `ClassificationResult` records for that job and excludes all finished products:
     ```python
     done_product_ids = set(ClassificationResult.objects.filter(job=job, status=Status.DONE).values_list('product_id', flat=True))
     pending_products = [p for p in all_products if p.id not in done_product_ids]
     ```
   - Processing resumes exactly from the first unfinished product with zero duplicate work.

---

## 12. Technology Choices and Reasoning

| Technology | Role | Rationale |
|---|---|---|
| **Python 3.12 + Django 5** | Core Backend | Mature ORM, built-in admin, robust migration system, and first-class DRF ecosystem. |
| **MariaDB 11.4** | Relational Database | ACID compliance, fast indexing on taxonomy trees, utf8mb4 full unicode support, and JSON column capabilities. |
| **Redis 7 + Celery** | Task Queue & Caching | Non-blocking background worker execution for 10,000+ item batch processing. |
| **Sentence-Transformers** | Text Embeddings | High semantic accuracy on product titles and descriptions with low latency (~15ms per SKU on CPU). |
| **OpenCLIP ViT-B-32** | Zero-Shot Vision | Strong multimodal image-text alignment for e-commerce catalog photographs. |
| **RapidFuzz** | Fuzzy String Matching | High-performance C++ backend for attribute extraction and keyword re-ranking. |
| **React 18 + Vite 5** | Curator Frontend | Instant HMR development, fast production bundle (<270kB), responsive UI, and stateful URL synchronization. |

---

## 13. High-Level Architecture

```
[Supplier Catalog (.xlsx / .csv)] 
               │
               ▼
   [ExcelCatalogParser] ──► Normalizes SKUs, 20-image arrays, prices & descriptions
               │
               ▼
       [Product Model] ──► MariaDB Catalog Storage
               │
               ▼
     [BatchProcessor] ──► Background Celery Worker (100-item chunks)
               │
   ┌───────────┴───────────────────────────────┐
   ▼                                           ▼
[TextClassifier]                        [ImageClassifier]
Sentence-Transformers                   OpenCLIP ViT-B-32
14.6k Pre-indexed Vectors               Zero-Shot Candidate Matching
   │                                           │
   └───────────────────┬───────────────────────┘
                       ▼
              [Multimodal Fusion]
         (60% Text + 40% Image Score)
                       │
                       ▼
             [ConfidenceEvaluator]
         • Modality completeness
         • Sibling ambiguity gap
         • < 0.55 review triggers
                       │
                       ▼
          [Attribute Extractor]
         RapidFuzz + Regex against
         allowed Shopify attribute schemas
                       │
                       ▼
          [ClassificationResult]
         MariaDB Persistence with
         Curator Approval Flags
                       │
                       ▼
    [React 18 Curation Dashboard]
    Overview KPIs ⇄ Review Queue ⇄ Import ⇄ Taxonomy Explorer
```

---

## 14. Realistic Development Effort Estimation, Assumptions, Dependencies, and Risks

### Effort Estimation:
- **Total Development Time:** 163 engineering hours (~4 weeks for a senior full-stack engineer and QA/DevOps specialist).
- **Breakdown:** Ingestion & DB (18h), Taxonomy (13h), Multi-modal AI (32h), Processing & Scalability (22h), REST APIs (16h), React UI (28h), QA/Testing (20h), DevOps & CI/CD (14h).

### Assumptions:
1. Supplier spreadsheets contain at least a unique SKU or Product Number column.
2. Standard CPU compute handles inference at 15–25ms/SKU; GPU compute accelerates processing to <5ms/SKU.

### Dependencies & Risks:
- **Dependency:** Pre-loaded Shopify taxonomy dataset (14,606 categories).
- **Risk Mitigation:** Missing/unreachable external images trigger non-blocking fallback to text semantic classification with calibrated confidence penalties.
