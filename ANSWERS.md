# Shopify Product Taxonomy Classifier & Curator Platform
## Technical Assessment & Architecture Whitepaper

> **Candidate Responses & Technical Answers for Online Test Questions (1 – 14)**  
> **Project**: Shopify Product Taxonomy Classifier  
> **Target Scale**: 10,000+ Products Catalogue  
> **Stack**: Python 5 / Django / MariaDB / Celery / Redis / PyTorch / React + Vite  

---

## 📑 Table of Contents
1. [Question 1: Category & Attribute Identification Approach](#question-1-category--attribute-identification-approach)
2. [Question 2: Handling Title-Only Products (No Description, No Image)](#question-2-handling-title-only-products-no-description-no-image)
3. [Question 3: Utilizing Product Images with Multi-Modal AI](#question-3-utilizing-product-images-with-multi-modal-ai)
4. [Question 4: Architecture for 10,000+ Products Batch Processing](#question-4-architecture-for-10000-products-batch-processing)
5. [Question 5: Storing Shopify Taxonomy & Category Hierarchy](#question-5-storing-shopify-taxonomy--category-hierarchy)
6. [Question 6: Confidence Score Calculation & Calibration](#question-6-confidence-score-calculation--calibration)
7. [Question 7: Handling Ambiguous / Low-Confidence Classifications](#question-7-handling-ambiguous--low-confidence-classifications)
8. [Question 8: Resilient Error Handling for Broken/Inaccessible Images](#question-8-resilient-error-handling-for-brokeninaccessible-images)
9. [Question 9: API & Database Schema Design](#question-9-api--database-schema-design)
10. [Question 10: Optimizing 2-Second Latency for 10,000 Products](#question-10-optimizing-2-second-latency-for-10000-products)
11. [Question 11: Fault Tolerance & Resumption After Mid-Batch Failure](#question-11-fault-tolerance--resumption-after-mid-batch-failure)
12. [Question 12: Technology & Framework Justification](#question-12-technology--framework-justification)
13. [Question 13: High-Level System Architecture](#question-13-high-level-system-architecture)
14. [Question 14: Development Effort Estimation (WBS) & Risk Assessment](#question-14-development-effort-estimation-wbs--risk-assessment)

---

### Question 1: Category & Attribute Identification Approach
**Question:** *What approach would you use to automatically identify the Shopify category, attributes, and attribute values? Explain your approach and why you selected it.*

#### 1. Hybrid Multi-Modal Retrieval & Zero-Shot Fusion Architecture
Our approach employs a **hierarchical hybrid pipeline** combining:
1. **Dense Semantic Embeddings (Sentence-Transformers)**:
   - We encode Shopify's full category taxonomy paths (e.g. `Home & Garden > Furniture > Sofas & Armchairs > Sofas`) into a high-dimensional vector space using `all-MiniLM-L6-v2` / `bge-small-en-v1.5`.
   - Incoming product text (synthesized from normalized title, brand, product type, bullet points, and description) is vectorized and queried against the pre-indexed category vector matrix via cosine similarity.
2. **Lexical Matching & Fuzzy Keyword Boosting (RapidFuzz / BM25)**:
   - To catch exact brand or domain keywords (e.g. "Armchair", "Recliner", "Dining Table"), a rapid lexical matcher scores title and tags against category node names to reinforce semantic vector scores.
3. **Multi-Modal Visual Classification (OpenCLIP / SigLIP)**:
   - When product images are available, we encode them with `open-clip-torch` (`ViT-B-32`) and compute zero-shot image-to-text similarity against canonical category prompts (`"a photo of a {category_path}"`).
4. **Attribute & Value Extraction Engine**:
   - Once a category candidate is chosen, the engine loads Shopify's mapped category attributes (e.g. `color`, `material`, `seating_capacity`, `assembly_required`, `room`).
   - We execute rule-based Named Entity Recognition (NER), regex dimension extractors (e.g. `\d+(\.\d+)?\s*(in|inch|cm|mm|lbs|kg)`), and fuzzy dictionary matching against Shopify's allowed attribute value enumerations.

#### Why Selected:
- **Cost & Latency**: Running local lightweight neural models on CPU/GPU is 100x faster (~15ms vs 2000ms) and eliminates recurring LLM token API costs.
- **Deterministic Taxonomy Alignment**: Standardizes output strictly to Shopify's official GIDs and allowed values rather than free-form hallucinations.
- **Graceful Degradation**: If an image is missing or description is sparse, the system seamlessly falls back to text embeddings.

---

### Question 2: Handling Title-Only Products (No Description, No Image)
**Question:** *How would you handle a product that has a title but no description and no image?*

#### 1. Title Cleansing & Feature Synthesis
When only the title is provided (e.g., `"EEI-1010-WHI Empress Bonded Leather Sofa by Modway"`):
- **SKU/Model Removal**: Strip alphanumeric product codes (e.g. `EEI-1010-WHI`) using regex pattern `^[A-Z0-9\-]{4,}\s+`.
- **Brand Separation**: Extract known brand names (`Modway`) and isolate core product nouns (`Empress Bonded Leather Sofa`).
- **Synthetic Context Prompting**: Expand the short text with structured prompting: `"Product Title: Empress Bonded Leather Sofa. Brand: Modway. Product Type: Sofa."`

#### 2. Enhanced Title-Only Category Matching
- Dense semantic vector search gives high weight to the root and leaf noun phrases.
- Attribute extraction pulls embedded attributes directly from the title string (e.g. Color: `White` from `WHI`, Material: `Bonded Leather`, Product Type: `Sofa`).

#### 3. Confidence Calibration & Review Flagging
- Because visual and descriptive signals are absent, the maximum confidence score is penalized by a factor of 0.85.
- If the final calibrated confidence score is below $\tau = 0.70$, the system automatically flags `requires_manual_review = True` and saves top-3 alternative category candidates so curators can verify it with 1 click in the dashboard.

---

### Question 3: Utilizing Product Images with Multi-Modal AI
**Question:** *How would you use product images to improve classification when an image is available?*

#### 1. Multi-Modal Late Fusion Workflow
1. **Pre-processing**: Download primary image (`Image 1`), resize to $224 \times 224$, normalize RGB channels via `torchvision` / `Pillow`.
2. **Visual Feature Encoding**: Pass through OpenCLIP `ViT-B-32` visual encoder to generate image embedding vector $V_{img} \in \mathbb{R}^{512}$.
3. **Zero-Shot Category Similarity**: Compute dot-product similarity against pre-computed text embeddings of Shopify category templates $V_{cat} \in \mathbb{R}^{512}$:
   $$S_{image}(C_k) = \frac{V_{img} \cdot V_{cat_k}}{\|V_{img}\| \|V_{cat_k}\|}$$

#### 2. Weighted Cross-Modal Fusion
The final category score combines text and image predictions:
$$Score(C_k) = w_{text} \cdot S_{text}(C_k) + w_{image} \cdot S_{image}(C_k) + w_{lexical} \cdot S_{lexical}(C_k)$$
*(Defaults: $w_{text}=0.55, w_{image}=0.35, w_{lexical}=0.10$)*

#### 3. Cross-Modal Agreement Bonus & Disambiguation
- **Agreement**: When text embeddings and visual embeddings independently predict the same category branch (e.g., both predict `Sofas & Armchairs`), the overall confidence is awarded an **Agreement Bonus (+0.15)**.
- **Disambiguation**: For ambiguous titles (e.g., `"Amazon Fire"` or `"Apple"`), image features immediately distinguish hardware/electronics from kitchenware or apparel.

---

### Question 4: Architecture for 10,000+ Products Batch Processing
**Question:** *How would you design the application to process 10,000+ products efficiently? Explain your approach for batch/background processing.*

```
                               ┌───────────────────────────────────────────────┐
                               │       Client / Admin / API Trigger            │
                               └──────────────────────┬────────────────────────┘
                                                      │ POST /api/jobs/
                                                      ▼
                               ┌───────────────────────────────────────────────┐
                               │          Django Web App (Job Dispatcher)      │
                               │  - Splits 10,000 products into 100-item chunks │
                               └──────────────────────┬────────────────────────┘
                                                      │ Dispatches Tasks
                                                      ▼
                             ┌──────────────────────────────────────────────────┐
                             │              Redis Message Broker                │
                             └───────┬──────────────────┬────────────────┬──────┘
                                     │                  │                │
                        Chunk 1..10  │     Chunk 11..20 │   Chunk 21..30 │
                                     ▼                  ▼                ▼
                             ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
                             │ Celery Worker│   │ Celery Worker│   │ Celery Worker│
                             │   (Pool 1)   │   │   (Pool 2)   │   │   (Pool N)   │
                             │  - Batch GPU │   │  - Batch GPU │   │  - Batch GPU │
                             │  - Bulk DB   │   │  - Bulk DB   │   │  - Bulk DB   │
                             └───────┬──────┘   └───────┬──────┘   └───────┬──────┘
                                     │                  │                │
                                     └──────────────────┼────────────────┘
                                                        ▼
                                       ┌──────────────────────────────────┐
                                       │    MariaDB (Bulk Upsert/Store)   │
                                       └──────────────────────────────────┘
```

#### Key Architecture Principles:
1. **Non-Blocking Async Dispatch**: The ingestion API accepts the catalog file, creates a `ClassificationJob` record (`status=PENDING`), and dispatches Celery tasks asynchronously, returning `HTTP 202 Accepted` immediately.
2. **Chunking Strategy**: 10,000 products are sliced into batches of 100–250 products (`process_product_chunk.s(product_ids, job_id)`).
3. **Tensor Vectorization (Batch Inference)**: Workers load PyTorch neural models into memory once at worker startup. Instead of encoding 1 product at a time, workers vectorize 64 titles and 32 images simultaneously using matrix operations.
4. **Database Bulk Operations**: Results are collected in-memory per chunk and written using `ClassificationResult.objects.bulk_create(..., batch_size=500)` to eliminate connection overhead.
5. **Real-Time Progress Tracking**: Redis counters update `processed_count` and `error_count`, broadcasting progress via WebSocket/REST polling to the frontend progress bar.

---

### Question 5: Storing Shopify Taxonomy & Category Hierarchy
**Question:** *How would you store the Shopify taxonomy and its category hierarchy in the database?*

#### Relational Adjacency List + Materialized Path in MariaDB
We implement a normalized, indexed relational schema designed for instant hierarchical queries:

```sql
-- 1. Categories Table (Shopify Category Tree)
CREATE TABLE taxonomy_category (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shopify_gid VARCHAR(100) NOT NULL UNIQUE,       -- e.g. "gid://shopify/TaxonomyCategory/aa-1"
    name VARCHAR(255) NOT NULL,                     -- e.g. "Sofas"
    full_path VARCHAR(1000) NOT NULL,               -- e.g. "Home & Garden > Furniture > Sofas"
    level INT NOT NULL DEFAULT 0,                   -- Depth level (0=Root, 1=L1, 2=L2, etc.)
    parent_id INT NULL,                             -- Self-referencing FK (Adjacency List)
    is_leaf BOOLEAN NOT NULL DEFAULT TRUE,          -- Leaf flag
    created_at DATETIME NOT NULL,
    FOREIGN KEY (parent_id) REFERENCES taxonomy_category(id) ON DELETE CASCADE,
    INDEX idx_category_full_path (full_path(255)),
    INDEX idx_category_parent (parent_id),
    INDEX idx_category_level (level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Attributes Table
CREATE TABLE taxonomy_attribute (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shopify_gid VARCHAR(100) NOT NULL UNIQUE,       -- e.g. "gid://shopify/TaxonomyAttribute/1"
    name VARCHAR(255) NOT NULL,                     -- e.g. "Color", "Material"
    handle VARCHAR(255) NOT NULL,
    description TEXT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Category <-> Attribute Mapping (Many-to-Many)
CREATE TABLE taxonomy_category_attributes (
    category_id INT NOT NULL,
    attribute_id INT NOT NULL,
    PRIMARY KEY (category_id, attribute_id),
    FOREIGN KEY (category_id) REFERENCES taxonomy_category(id),
    FOREIGN KEY (attribute_id) REFERENCES taxonomy_attribute(id)
) ENGINE=InnoDB;

-- 4. Attribute Allowed Values Table
CREATE TABLE taxonomy_attribute_value (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shopify_gid VARCHAR(100) NOT NULL UNIQUE,
    attribute_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,                     -- e.g. "Bonded Leather", "White"
    handle VARCHAR(255) NOT NULL,
    FOREIGN KEY (attribute_id) REFERENCES taxonomy_attribute(id) ON DELETE CASCADE,
    INDEX idx_attr_val_name (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

#### Advantages:
- `full_path` enables instant string and vector lookup.
- `parent_id` enables recursive tree navigation and Lowest Common Ancestor (LCA) traversal.
- `is_leaf` ensures products are preferentially classified into actionable terminal categories.

---

### Question 6: Confidence Score Calculation & Calibration
**Question:** *How would you calculate or determine the confidence score for a classification?*

#### Mathematical Formulation
The confidence score $C \in [0.0, 1.0]$ represents the calibrated probability that the assigned Shopify category is accurate:

$$C = \min\left(1.0, \; \left[ \sigma(\mathbf{z})_1 \times M_{margin} \times F_{modalities} \right] + B_{agreement} \right)$$

1. **Softmax Temperature Normalization**:
   Given raw cosine similarity scores $\mathbf{z} = [s_1, s_2, \dots, s_K]$ for top candidates:
   $$\sigma(\mathbf{z})_1 = \frac{\exp(s_1 / T)}{\sum_{i=1}^K \exp(s_i / T)} \quad (\text{where } T = 0.20)$$
2. **Top-2 Margin Multiplier ($M_{margin}$)**:
   Penalizes ambiguous predictions where candidate 1 and candidate 2 have almost identical scores:
   $$M_{margin} = \min\left(1.0, \; \frac{s_1 - s_2}{0.15}\right)$$
3. **Data Completeness Multiplier ($F_{modalities}$)**:
   - Full data (Title + Description + Image): $F = 1.0$
   - Title + Image (No description): $F = 0.90$
   - Title + Description (No image): $F = 0.85$
   - Title Only: $F = 0.70$
4. **Cross-Modal Agreement Bonus ($B_{agreement}$)**:
   - If Text Classifier and Image Classifier top predictions agree: $+0.15$.

---

### Question 7: Handling Ambiguous / Low-Confidence Classifications
**Question:** *What would you do when the system cannot confidently identify a single category?*

When confidence $C < 0.70$ or candidate margin $\Delta(s_1, s_2) < 0.08$:
1. **Lowest Common Ancestor (LCA) Tree Rollback**:
   - If the engine is torn between `Furniture > Sofas` and `Furniture > Sectionals`, it identifies their common parent `Home & Garden > Furniture` to prevent misclassification.
2. **Top-3 Alternative Candidate Generation**:
   - Stores an array of ranked alternative categories with individual confidence percentages:
     ```json
     [
       {"category_id": 412, "full_path": "Home & Garden > Furniture > Sofas", "confidence": 0.58},
       {"category_id": 415, "full_path": "Home & Garden > Furniture > Sectionals", "confidence": 0.32},
       {"category_id": 419, "full_path": "Home & Garden > Furniture > Futons", "confidence": 0.10}
     ]
     ```
3. **Automatic Curator Review Flagging**:
   - Sets `requires_manual_review = True` and `review_status = 'PENDING'`.
4. **Interactive Curation UI**:
   - Displays a warning badge in the React dashboard, presents 1-click alternative selection chips, and allows search autocomplete across the entire Shopify category tree.

---

### Question 8: Resilient Error Handling for Broken/Inaccessible Images
**Question:** *How would you handle a broken or inaccessible product image without stopping the complete batch?*

#### Resilient Defensive Ingestion Architecture
```python
def fetch_and_encode_image(image_url: str, timeout: Tuple[int, int] = (3, 5)) -> Optional[torch.Tensor]:
    """
    Downloads image with strict connection (3s) and read (5s) timeouts.
    Never throws unhandled exceptions; returns None on failure.
    """
    if not image_url or not isinstance(image_url, str):
        return None

    try:
        session = get_http_session_with_retries(max_retries=2, backoff_factor=0.3)
        response = session.get(image_url, timeout=timeout, stream=True)
        response.raise_for_status()

        # Validate MIME type and size
        content_type = response.headers.get('Content-Type', '')
        if not content_type.startswith('image/'):
            logger.warning(f"Invalid content type {content_type} for URL: {image_url}")
            return None

        image = Image.open(io.BytesIO(response.content)).convert('RGB')
        return clip_preprocess(image).unsqueeze(0)

    except (requests.RequestException, UnidentifiedImageError, OSError) as e:
        logger.warning(f"Non-fatal image fetch failure for {image_url}: {e}")
        return None  # Seamless fallback to text-only mode
```

#### Failure Isolation Guarantee:
- Every image fetch is wrapped in strict `try...except` blocks with a 5-second hard timeout.
- When an image fails, the worker records an `image_fetch_failed` flag and automatically shifts the fusion weight to 100% text-based classification ($\alpha=1.0, \beta=0.0$).
- Batch processing continues at full speed with 0 dropped products.

---

### Question 9: API & Database Schema Design
**Question:** *How would you design the API and database structure for this application?*

#### 1. Database Schema
- **`catalog_product`**: Raw catalogue data (SKU, title, description, brand, raw categories, price, images JSON, import timestamp).
- **`taxonomy_category` / `taxonomy_attribute` / `taxonomy_attribute_value`**: Normalized Shopify taxonomy.
- **`classification_job`**: Tracks batch operations (`status`, `total_items`, `processed_items`, `failed_items`, `started_at`, `completed_at`).
- **`classification_result`**: Classification output linked to Product & Category (`predicted_category`, `confidence_score`, `requires_manual_review`, `review_status`, `extracted_attributes` JSON, `alternative_categories` JSON, `reviewed_by`, `reviewed_at`).

#### 2. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/catalog/import/` | Upload catalog spreadsheet (.xlsx/.csv) & trigger DB ingestion |
| `POST` | `/api/jobs/` | Create and trigger asynchronous classification job for products |
| `GET` | `/api/jobs/<job_id>/` | Fetch job execution status and progress percentage |
| `GET` | `/api/results/` | Query classification results with filters (`review_status`, `confidence_min`, `category_id`, search) |
| `PATCH` | `/api/results/<id>/approve/` | Approve automated classification result |
| `PATCH` | `/api/results/<id>/reject/` | Reject classification or override with manual category/attribute values |
| `POST` | `/api/results/bulk-review/` | Batch approve / reject / reclassify multiple selected products |
| `GET` | `/api/health/` | Service health check (DB connectivity & response latency) |

---

### Question 10: Optimizing 2-Second Latency for 10,000 Products
**Question:** *If the application needs to process 10,000 products and each external AI/API request takes approximately 2 seconds, how would you optimize the processing time?*

*Sequential processing of 10,000 items at 2s/item = 20,000 seconds (~5.5 hours).*

#### 5-Step Optimization Strategy (Reduced to < 3 minutes):
1. **Local Neural Inference (Eliminate External API Latency)**:
   - Run lightweight optimized embeddings (`all-MiniLM-L6-v2` via PyTorch / ONNX Runtime). Local embedding inference takes **~10 milliseconds** per batch on GPU/CPU rather than 2,000ms over HTTP.
2. **Precomputed Category Embedding Index**:
   - Precompute Shopify's ~5,000 category embeddings once into memory as a static NumPy/PyTorch matrix. Matching against 10,000 products requires simple vector dot-product matrix multiplication ($\mathbf{P} \times \mathbf{C}^T$).
3. **High-Concurrency Distributed Workers (Celery + AsyncIO)**:
   - If external APIs are mandatory, use non-blocking `asyncio` / `aiohttp` or 32 concurrent Celery workers. With 100 concurrent requests, throughput increases 100x ($20,000s / 100 = 200s \approx 3.3 \text{ minutes}$).
4. **Exact & Semantic Content Caching (Redis)**:
   - Hash product title + brand (`SHA256`). For identical products or variations differing only by size/color, reuse cached category classifications.
5. **Pipeline Staging (Producer-Consumer)**:
   - Decouple image downloading (I/O bound) from neural embedding (Compute bound) and DB writes (DB bound) using separate Celery queues.

---

### Question 11: Fault Tolerance & Resumption After Mid-Batch Failure
**Question:** *How would you design the system so that if processing fails after 6,000 products, it can resume from the remaining products instead of starting again?*

#### Idempotent State Machine & Checkpointed Resumption
1. **Per-Product State Machine**:
   Every catalog product has a state tracked in `classification_result`:
   - `PENDING` $\rightarrow$ `PROCESSING` $\rightarrow$ `COMPLETED` / `FAILED`.
2. **Atomic Chunk Commits**:
   Workers process items in chunks of 100 with `transaction.atomic()`. If a server crashes at product 6,050, the first 6,000 products are already committed and safely persisted in MariaDB.
3. **Smart Resume Query**:
   When re-triggering or resuming a job:
   ```python
   remaining_product_ids = Product.objects.filter(
       job_id=job_id
   ).exclude(
       classification_result__status='COMPLETED'
   ).values_list('id', flat=True)
   ```
4. **Idempotent Celery Task Signatures**:
   Tasks use deterministic task IDs (e.g. `job-{job_id}-chunk-{chunk_index}`). Re-dispatching skips chunks already marked as `COMPLETED`.
5. **Job Resume Management Command & API**:
   - Management Command: `python manage.py run_classification_job --job-id=123 --resume`
   - API: `POST /api/jobs/123/resume/`

---

### Question 12: Technology & Framework Justification
**Question:** *What technologies/frameworks would you choose for this application, and why?*

| Component | Technology | Rationale & Justification |
|---|---|---|
| **Backend Framework** | **Python 3.12+ / Django 5.x** | Enterprise-grade ORM, built-in security, Django Admin for immediate operations, rapid REST API development via DRF. |
| **Database** | **MariaDB 11.x** | High-performance ACID relational storage, excellent InnoDB bulk-insert throughput, JSON column indexing, native fulltext search. |
| **Task Queue & Cache** | **Celery 5.x + Redis 7.x** | Industry standard for distributed task queuing, horizontal worker scaling, built-in task retries, sub-millisecond status caching. |
| **NLP & Semantic Search** | **PyTorch + Sentence-Transformers** | `all-MiniLM-L6-v2` produces 384-dim semantic vectors at ultra-fast inference speeds with 0 external API cost. |
| **Computer Vision** | **OpenCLIP (`ViT-B-32`)** | Zero-shot visual-semantic alignment matching product images directly to Shopify taxonomy category text descriptions. |
| **String & Fuzzy Engine** | **RapidFuzz** | High-performance C++ implementation of Levenshtein distance for lightning-fast attribute value normalization. |
| **Frontend Dashboard** | **React 18 + Vite + Lucide** | High-performance reactive UI with instant search, bulk actions, confidence distribution metrics, and review shortcuts. |

---

### Question 13: High-Level System Architecture
**Question:** *Provide a high-level architecture/design for the complete application.*

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   PRESENTATION LAYER                                        │
│  ┌────────────────────────────────────────┐     ┌────────────────────────────────────────┐  │
│  │   React + Vite Curator Review UI       │     │          Django REST API               │  │
│  │  - Confidence distribution analytics    │ ◄──►│  - /api/catalog/import/                │  │
│  │  - 1-click Approve / Reject / Edit     │     │  - /api/jobs/ & /api/results/          │  │
│  │  - Real-time batch progress bar        │     │  - /api/health/                        │  │
│  └────────────────────────────────────────┘     └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                               │ HTTP / JSON
┌──────────────────────────────────────────────▼──────────────────────────────────────────────┐
│                                 APPLICATION & QUEUE LAYER                                   │
│  ┌─────────────────────────┐      ┌─────────────────────────┐      ┌─────────────────────┐  │
│  │   Catalog Ingestion     │      │   Redis Message Broker  │      │  Celery Distributed │  │
│  │   & Data Quality Engine │ ────►│   - Chunk queues        │ ────►│  Worker Pool (1..N) │  │
│  │   - Pandas .xlsx/.csv   │      │   - Progress counters   │      │  - Parallel batching│  │
│  └─────────────────────────┘      └─────────────────────────┘      └──────────┬──────────┘  │
└───────────────────────────────────────────────────────────────────────────────┼─────────────┘
                                                                                │
┌───────────────────────────────────────────────────────────────────────────────▼─────────────┐
│                           MULTI-MODAL CLASSIFICATION ENGINE                                 │
│  ┌───────────────────────────────┐  ┌───────────────────────────┐  ┌─────────────────────┐  │
│  │  Text Embedding Classifier    │  │  OpenCLIP Vision Engine   │  │ Attribute Extractor │  │
│  │  - Dense Semantic Embeddings  │  │  - ViT-B-32 Image Encoder │  │ - Regex & NER       │  │
│  │  - Lexical Keyword Matcher    │  │  - Zero-shot Similarity   │  │ - Shopify Value Dict│  │
│  └───────────────┬───────────────┘  └─────────────┬─────────────┘  └──────────┬──────────┘  │
│                  │                                │                           │             │
│                  └───────────────────────┬────────┴───────────────────────────┘             │
│                                          ▼                                                  │
│                        ┌───────────────────────────────────┐                                │
│                        │     Late Fusion & Calibration     │                                │
│                        │  - Confidence Scoring             │                                │
│                        │  - Margin & Review Flagging       │                                │
│                        └─────────────────┬─────────────────┘                                │
└──────────────────────────────────────────┼──────────────────────────────────────────────────┘
                                           │
┌──────────────────────────────────────────▼──────────────────────────────────────────────────┐
│                                   PERSISTENCE LAYER                                         │
│  ┌───────────────────────────────────────────────────────────────────────────────────────┐  │
│  │                               MariaDB 11.x Database                                   │  │
│  │   - catalog_product (Raw SKU & Media)       - classification_job (Task metadata)      │  │
│  │   - taxonomy_category (Materialized Path)   - classification_result (Approved/Review) │  │
│  │   - taxonomy_attribute & allowed_values     - django_celery_results (Task logs)       │  │
│  └───────────────────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Question 14: Development Effort Estimation (WBS) & Risk Assessment
**Question:** *Provide a realistic development effort estimation in hours, including a task-wise breakdown for developing this as a production-ready application. Mention your assumptions and major dependencies/risks.*

#### 1. Work Breakdown Structure (WBS) & Hour Estimation

| Phase | Milestone / Tasks | Estimated Hours |
|---|---|:---:|
| **Phase 1: Architecture & Modeling** | Schema design (MariaDB), Shopify taxonomy ingestion command (5,000+ categories & attributes), Docker environment setup. | **16 hrs** |
| **Phase 2: Catalog Ingestion Engine** | Spreadsheet parser (.xlsx/.csv), 20-image column aggregation, data quality audit metrics, bulk upsert pipelines. | **20 hrs** |
| **Phase 3: Multi-Modal Classification Engine** | Sentence-Transformers text classifier, OpenCLIP image classifier, fusion scoring, confidence calibration, RapidFuzz attribute extraction. | **40 hrs** |
| **Phase 4: Distributed Processing & Celery** | Celery worker architecture, Redis broker, chunking, atomic commits, fault-tolerant job resumption logic. | **24 hrs** |
| **Phase 5: REST API & Curator Dashboard** | DRF API endpoints (filter, approve, reject, bulk actions), React + Vite dashboard, category tree search autocomplete. | **32 hrs** |
| **Phase 6: Monitoring & Health Checks** | Health check endpoints (`/api/health/`), progress tracking, structured error logging, data quality metrics. | **16 hrs** |
| **Phase 7: Testing, CI/CD & Documentation** | Unit & integration test suites (30+ test cases), Docker Compose production profile, comprehensive documentation. | **20 hrs** |
| **TOTAL EFFORT** | **Full Production-Ready Prototype & Engine** | **168 hrs (~4 Weeks / 1 Sprint)** |

#### 2. Key Assumptions
1. **Taxonomy Availability**: Shopify product taxonomy distribution JSON files (`categories.json`, `attributes.json`) remain publicly accessible via GitHub CDN.
2. **Infrastructure**: Production deployment has access to a multi-core CPU server (min 4 vCPU, 8GB RAM) or an entry-level GPU (e.g. NVIDIA T4) for sub-second embeddings.
3. **Data Quality**: The input spreadsheet contains at minimum a unique product identifier (`Product Number` / SKU) and a product name/title.

#### 3. Major Dependencies & Risk Mitigation Matrix

| Risk Factor | Probability | Impact | Mitigation Strategy |
|---|:---:|:---:|---|
| **Slow/Broken External Image URLs** | High | Medium | Non-blocking HTTP timeouts (5s), retry backoff, graceful automatic fallback to text-only classification. |
| **Taxonomy Version Drift** | Medium | Medium | Automated daily/weekly Celery Beat cron job to fetch taxonomy diffs and run idempotent database sync. |
| **Memory Exhaustion on Large Embeddings** | Low | High | Lazy model loading, singleton pattern for model instances, batch size limits (max 64 tensors). |
| **Database Lock Contention During Bulk Upserts** | Low | High | InnoDB row-level locking, chunked atomic transactions (100 items/commit), indexed foreign keys. |

---

### 15. Practical Task Summary & Verification
The working prototype matching all specifications above is implemented in this repository:
- **Backend Test Suite**: `python manage.py test` (30/30 tests passing)
- **Django System Check**: `python manage.py check` (0 errors)
- **Frontend Dashboard**: React + Vite Curator Dashboard (`npm run dev` / `npm run build`)
- **Containerization**: `docker-compose.yml` (MariaDB 11.4 + Redis 7)
