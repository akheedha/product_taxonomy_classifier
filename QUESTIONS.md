# 📌 TECHNICAL DESIGN QUESTIONS & ANSWERS

This document provides complete, direct answers to the **14 core technical and architectural design questions** for the **Shopify Product Taxonomy Classifier & Human Curation Platform**.

---

## 📑 Table of Questions

1. [Question 1: Automatic Shopify Category, Attributes & Attribute Values](#question-1-automatic-shopify-category-attributes--attribute-values)
2. [Question 2: Handling a Product With Only a Title (No Description or Image)](#question-2-handling-a-product-with-only-a-title-no-description-or-image)
3. [Question 3: Using Product Images for Visual Categorization](#question-3-using-product-images-for-visual-categorization)
4. [Question 4: Large-Scale Processing of 10,000+ Products](#question-4-large-scale-processing-of-10000-products)
5. [Question 5: Shopify Taxonomy Database Structure & Hierarchy](#question-5-shopify-taxonomy-database-structure--hierarchy)
6. [Question 6: Determining Classification Confidence Score](#question-6-determining-classification-confidence-score)
7. [Question 7: Handling Uncertain or Multiple Category Results](#question-7-handling-uncertain-or-multiple-category-results)
8. [Question 8: Handling Broken or Inaccessible Images](#question-8-handling-broken-or-inaccessible-images)
9. [Question 9: API and Database Architecture](#question-9-api-and-database-architecture)
10. [Question 10: Optimizing 10,000 AI/API Requests](#question-10-optimizing-10000-aiapi-requests)
11. [Question 11: Resuming After Failure at 6,000 of 10,000 Products](#question-11-resuming-after-failure-at-6000-of-10000-products)
12. [Question 12: Technology & Framework Choices](#question-12-technology--framework-choices)
13. [Question 13: High-Level System Architecture](#question-13-high-level-system-architecture)
14. [Question 14: Production Development Effort Estimation (Hours & WBS)](#question-14-production-development-effort-estimation-hours--wbs)
15. [Current Prototype vs Production Architecture Comparison](#current-prototype-vs-production-architecture-comparison)

---

## Question 1: Automatic Shopify Category, Attributes & Attribute Values

> **Question:**  
> *Explain the approach used to automatically identify:*
> - *Shopify category*
> - *Category attributes*
> - *Attribute values*
> 
> *Explain the complete classification pipeline. Cover how the system uses available product title, description, product type, brand, image, and Shopify taxonomy. Explain why this approach was selected and discuss fallback behavior when some information is unavailable.*

### Answer:

The system uses a **multi-stage hybrid semantic search, visual zero-shot inference, late fusion, and fuzzy token matching pipeline**:

```mermaid
flowchart TD
    A[Raw Product Record\nTitle, Brand, Category, Specs, Image] --> B[Data Normalization & Cleaning\nimports/excel_parser.py]
    B --> C[Text Query Synthesizer\nclassification/engine/text_classifier.py]
    C --> D[Dense Semantic Embedding\nSentenceTransformers all-MiniLM-L6-v2]
    D --> E[Cosine Similarity Vector Dot Product\nAgainst 14,606 Cached Taxonomy Vectors]
    E --> F[Top-5 Candidate Category Extraction]
    
    A -.-> G{Image Available\n& Valid?}
    G -- Yes --> H[OpenCLIP ViT-B-32 Zero-Shot Visual Inference\nclassification/engine/image_classifier.py]
    H --> I[Prompt Generation for Top-5 Candidates]
    I --> J[Image-Text Cosine Similarity Matrix]
    J --> K[Late Fusion Scoring Engine\nclassification/engine/fusion.py]
    G -- No / Error --> L[Text-Only Scoring Mode]
    F --> K
    F --> L
    
    K --> M[Final Category Ranking & Selection]
    L --> M
    
    M --> N[Category Attribute Resolution\nQuery Category + Ancestor Allowed Attributes]
    N --> O[Attribute Extractor\nRapidFuzz + Word-Boundary Regex Matcher]
    O --> P[Confidence Calculation & Review Heuristics\nclassification/confidence.py]
    P --> Q[Persist ClassificationResult\nMariaDB Database]
```

#### 1. Category Identification Pipeline
1. **Query Construction (`text_classifier.py`):** Available fields (`brand`, `product_name`, `product_category`, `product_sub_category`, `materials`, `product_color`, `product_description`) are synthesized into a high-density natural language string.
2. **Dense Vector Embedding (`SentenceTransformers all-MiniLM-L6-v2`):** Converts the product text into a 384-dimensional dense vector.
3. **Vector Matrix Dot Product:** The product embedding is multiplied against a pre-computed $14606 \times 384$ matrix of all Shopify taxonomy paths (`category_embeddings_all-MiniLM-L6-v2.npy`) to retrieve top semantic candidates in **12–18 ms**.
4. **Visual Rescoring (`OpenCLIP ViT-B-32`):** When an image is available, CLIP computes zero-shot similarity between the image and top-5 category candidate prompts (e.g. `"a product photo of Sofas, category Furniture > Sofas"`).
5. **Late Fusion (`fusion.py`):** Combines text score ($S_{\text{text}}$) and visual score ($S_{\text{image}}$):
   $$S_{\text{fused}} = 0.60 \cdot S_{\text{text}} + 0.40 \cdot S_{\text{image}}$$
   *(Falls back to $1.00 \cdot S_{\text{text}}$ if image is missing or download fails).*

#### 2. Category Attributes & Values Detection (`attribute_extractor.py`)
1. **Schema Retrieval:** Queries MariaDB for all allowed `Attribute` and `AttributeValue` entities associated with the predicted category and its ancestor chain (e.g. `Furniture > Sofas` inherits from `Furniture`).
2. **Value Extraction Algorithms:**
   - **Exact Matching:** Uses word-boundary regex (`\b{canonical_value}\b`) across title, description, and spec fields (confidence: `1.00`).
   - **Fuzzy Matching:** Uses `RapidFuzz` token set ratio with an 80% threshold (confidence: `ratio / 100`) to catch slight spelling differences and typos.
3. **Output:** Structured JSON mapping:
   ```json
   {
     "Color": {"value": "Gray", "confidence": 1.0, "source": "product_color"},
     "Material": {"value": "Upholstered Fabric", "confidence": 0.92, "source": "materials"}
   }
   ```

---

## Question 2: Handling a Product With Only a Title (No Description or Image)

> **Question:**  
> *Explain exactly how the system handles a product where:*
> - *Title exists*
> - *Description is missing*
> - *Image is missing*
> 
> *Explain: What information is still available, how classification proceeds, how attributes are inferred, how confidence is affected, and when manual review is triggered.*

### Answer:

When a catalog product contains only a title (e.g., `"Solid Teak Outdoor Dining Table"`):

1. **Available Information:**
   - Available: `product_name` (Title) and `product_number` (SKU), plus any supplier category strings if provided.
   - Missing: `product_description`, `primary_image`, `images`, `materials`, `product_color`, `bullets`.

2. **Classification Execution:**
   - The query synthesizer builds a sparse text query containing only the title and brand/type if present.
   - Dense vector embedding (`SentenceTransformers`) embeds the sparse title and performs vector dot product against the 14,606 taxonomy categories.
   - Zero-shot visual classification is skipped cleanly.

3. **Attribute Inference:**
   - `AttributeExtractor` searches for allowed attribute values strictly within n-grams of the product title (e.g., extracts `Material = "Teak"` and `Type = "Dining Table"`).

4. **Confidence Calibration Impact:**
   - The engine flags `is_low_info = True`.
   - A modality penalty multiplier ($0.70\times$) is applied in `classification/confidence.py`:
     $$\text{Confidence}_{\text{final}} = S_{\text{text}} \times 0.70$$

5. **Manual Review Routing:**
   - Products with `is_low_info = True` automatically receive `needs_manual_review = True` with the review reason:
     `"Low information product record (missing or brief description)"`.
   - The top 3 alternative category suggestions are saved in `alternative_categories` for 1-click curator override in the UI.

---

## Question 3: Using Product Images for Visual Categorization

> **Question:**  
> *Explain how images improve classification when an image is available. Cover image retrieval, validation, analysis, combining visual and textual information, visual signals influencing category/attribute identification, and what happens if image processing fails.*

### Answer:

1. **Image Retrieval & Validation (`image_classifier.py`):**
   - The system validates the URL scheme (`http`/`https`).
   - Downloads the image using a dedicated `requests.Session` with `urllib3` connection pooling, strict timeouts (**3.0s connect, 6.0s read**), and 2 retries with backoff.
   - Validates image integrity using `PIL.Image.open()` and converts color space to standard RGB.

2. **Zero-Shot Visual Analysis (`OpenCLIP ViT-B-32`):**
   - The image is preprocessed (Resize 224x224, CenterCrop, Normalize).
   - Top-5 category candidates from the text stage are converted into natural prompts: `"a product photo of {category_name}, category {breadcrumb_path}"`.
   - Computes cosine similarity between image embeddings (512-d) and prompt text embeddings.

3. **Combining Visual and Textual Information (Late Fusion):**
   - Combines normalized scores:
     $$S_{\text{fused}} = 0.60 \cdot S_{\text{text}} + 0.40 \cdot S_{\text{image}}$$
   - **Disambiguation Example:** If text is ambiguous between *Desk Chair* ($0.63$) and *Dining Chair* ($0.62$), the CLIP visual embedding scores the office ergonomic chair photo higher ($0.89$ vs $0.32$), pushing *Desk Chair* decisively to Rank 1.

4. **Failure Handling & Graceful Fallback:**
   - If an image returns 404, times out, or contains corrupted bytes, the exception is caught, a warning is logged, `used_image` is set to `False`, and the pipeline falls back to 100% text scoring without crashing the batch.

---

## Question 4: Large-Scale Processing of 10,000+ Products

> **Question:**  
> *Explain how the application efficiently processes 10,000+ products. Cover batching, background processing, concurrency, rate limits, retries, timeouts, database operations, progress tracking, failed products, and resumability. Why is processing everything inside a single HTTP request inappropriate?*

### Answer:

```mermaid
flowchart LR
    A[Frontend Dashboard] -->|POST /api/jobs/| B[Django REST API]
    B -->|Create ClassificationJob\nstatus: pending| C[(MariaDB Database)]
    B -->|Dispatch job.delay(job_id)| D[Redis Queue]
    B -- Return 201 Created\njob_id: 42 --> A
    
    D --> E[Celery Worker Cluster]
    E --> F[BatchProcessor\nprocessing/batch_processor.py]
    F -->|Chunk Iterator: 100 items| G[Product Chunk 1..N]
    G --> H[Multimodal Classification Engine]
    H -->|Atomic Checkpoint: every 5 items| C
    
    A -->|Poll GET /api/jobs/42/ every 2.5s| B
    B -->|Read progress_pct, status| A
```

### Why a Single HTTP Request Is Inappropriate:
- **HTTP Gateway Timeouts:** Nginx/Gunicorn terminate connections after 30–60s. 10,000 products take minutes to hours.
- **Memory Exhaustion:** Loading 10,000 full records and images in one process exceeds RAM limits.
- **Worker Starvation:** Synchronous HTTP threads remain blocked, preventing any other user from accessing the system.

### Implemented Architecture:
1. **Asynchronous Celery Workers:** Jobs are submitted via `POST /api/jobs/` and run asynchronously in Celery worker processes backed by Redis.
2. **Chunked Memory Streaming:** Products are streamed in chunks of 100 using `.iterator(chunk_size=100)` to maintain a flat memory footprint ($\le 350\text{ MB}$).
3. **Atomic Progress Checkpoints:** Every 5 processed products, the worker saves results to MariaDB and updates `job.processed_products` and `job.progress_pct`.
4. **Pre-Cached Vector Matrix in RAM:** All 14,606 category embeddings are pre-computed in memory. Text classification requires only a **15 ms matrix multiplication** per product.
5. **Per-Item Fault Isolation:** Any failure on product $N$ is caught and logged; the worker proceeds to product $N+1$.

---

## Question 5: Shopify Taxonomy Database Structure & Hierarchy

> **Question:**  
> *Explain how the Shopify Product Taxonomy and its hierarchy are stored in the database. Cover taxonomy categories, IDs, parent-child relationships, hierarchy traversal, attributes, attribute values, indexes, and relationships.*

### Answer:

The database schema in [backend/taxonomy/models.py](file:///d:/assignment/product_taxonomy_classifier/backend/taxonomy/models.py) implements the canonical Shopify Taxonomy schema in relational MariaDB:

```mermaid
erDiagram
    taxonomy_categories ||--o{ taxonomy_categories : "parent_id (hierarchy)"
    taxonomy_categories ||--o{ taxonomy_category_attributes : "maps"
    taxonomy_attributes ||--o{ taxonomy_category_attributes : "allowed_in"
    taxonomy_attributes ||--o{ taxonomy_attribute_values : "has_values"
    
    products ||--o{ classification_results : "classified_in"
    taxonomy_categories ||--o{ classification_results : "predicted_category"
    classification_jobs ||--o{ classification_results : "belongs_to"

    taxonomy_categories {
        string id PK "gid://shopify/TaxonomyCategory/aa-1"
        string name "Category leaf name"
        string full_name "Breadcrumb path (Indexed)"
        string parent_id FK "Self-referencing parent"
        int level "Tree depth 1..N"
        boolean is_leaf "Terminal node flag"
    }

    taxonomy_attributes {
        string id PK "gid://shopify/TaxonomyAttribute/1"
        string name "Attribute name (e.g. Color)"
        string handle "slug handle"
        string description "Attribute guidelines"
    }

    taxonomy_attribute_values {
        string id PK "gid://shopify/TaxonomyAttributeValue/101"
        string attribute_id FK
        string name "Canonical value (e.g. Navy Blue)"
        string handle "slug handle"
    }
```

### Key Schema Capabilities:
1. **Self-Referential Tree (`parent_id`):** Allows arbitrary tree depth. Supported by recursive helper methods `Category.get_ancestors()` and `Category.get_children()`.
2. **Indexed Breadcrumbs (`full_name`):** B-tree and Full-Text indexes on `full_name` support prefix search and instant UI autocomplete across 14,606 categories.
3. **Many-to-Many Attribute Inheritance:** Mappings in `taxonomy_category_attributes` allow child categories to inherit allowed attributes (e.g. *Material*, *Finish*) from parent taxonomy nodes.

---

## Question 6: Determining Classification Confidence Score

> **Question:**  
> *Explain how classification confidence is determined. What signals are used (model confidence, text evidence, image evidence, taxonomy match, information availability, agreement)? What are the exact thresholds for high, medium, low confidence, and manual review?*

### Answer:

Confidence is a calibrated score $C \in [0.0, 1.0]$ computed in [backend/classification/confidence.py](file:///d:/assignment/product_taxonomy_classifier/backend/classification/confidence.py):

$$\text{Confidence} = S_{\text{fused}} \times M_{\text{completeness}} \times P_{\text{distance}}$$

### 1. Signal Composition:
- **$S_{\text{fused}}$:** Late fusion similarity score between product representation and top category ($0.0 \dots 1.0$).
- **$M_{\text{completeness}}$:** Modality completeness multiplier:
  - Text + Image available: **$1.00\times$**
  - Title + Image available: **$0.90\times$**
  - Full Text Only (No Image): **$0.85\times$**
  - Title Only (Sparse Record): **$0.70\times$**
- **$P_{\text{distance}}$:** Sibling separation penalty (applied if Rank 1 and Rank 2 category scores are too close).

### 2. Calibrated Decision Thresholds:

| Confidence Tier | Score Range | System Action | Curation Workflow |
|---|---|---|---|
| **High Confidence** | $\ge 0.65$ | Auto-accepted | `needs_manual_review = False`. Bypasses review queue. |
| **Medium Confidence** | $0.55 \le \text{Score} < 0.65$ | Conditional | Accepted if sibling ambiguity gap $\ge 0.010$. Flagged for review if gap is narrow. |
| **Low Confidence** | $< 0.55$ | Review Required | `needs_manual_review = True`. Reason: `"Low classification confidence"`. |

---

## Question 7: Handling Uncertain or Multiple Category Results

> **Question:**  
> *Explain what happens when the system cannot confidently select one category. Cover confidence thresholds, alternative category suggestions, ranking, manual review flags, storage of uncertain classifications, and allowing a user to approve or correct the result.*

### Answer:

1. **Sibling Ambiguity Detection:**
   - The engine calculates the score gap between the top 2 candidates: $\Delta = S_{\text{rank1}} - S_{\text{rank2}}$.
   - If $\Delta < 0.010$ and $S_{\text{rank1}} < 0.65$, the system identifies the prediction as borderline ambiguous and flags:
     `"Ambiguous top candidates (gap between rank 1 and 2 is {gap:.4f} < 0.010)"`.

2. **Storing Alternative Categories:**
   - The top 3 alternative category suggestions are persisted in `ClassificationResult.alternative_categories`:
     ```json
     [
       {"category_id": "gid://shopify/TaxonomyCategory/aa-2", "name": "Sofas", "full_name": "Furniture > Sofas", "score": 0.7100},
       {"category_id": "gid://shopify/TaxonomyCategory/aa-3", "name": "Sofa Legs", "full_name": "Furniture > Sofa Accessories > Sofa Legs", "score": 0.7023},
       {"category_id": "gid://shopify/TaxonomyCategory/aa-4", "name": "Bean Bag Sofas", "full_name": "Furniture > Sofas > Bean Bag Sofas", "score": 0.6728}
     ]
     ```

3. **Curator Review & Override Workflow:**
   - In the React Review Workspace, curators filter records by `needs_review=true`.
   - Expanding a product row opens a side drawer displaying the image, specifications, detected attributes, and alternative candidate chips.
   - Curators can:
     - Click **Approve** to accept the predicted category (`PATCH /api/results/{id}/` with `{"approved": true}`).
     - Click any **Alternative Chip** to reassign the category.
     - Use the **Taxonomy Autocomplete** search to assign any category.
     - Overrides automatically set `confidence = 1.00` and `needs_manual_review = False`.

---

## Question 8: Handling Broken or Inaccessible Images

> **Question:**  
> *Explain how the application handles invalid image URLs, inaccessible images, timeouts, download failures, and processing errors. Detail how fault isolation ensures an image failure never stops the complete batch.*

### Answer:

```mermaid
flowchart TD
    A[Image URL Extracted] --> B{URL Scheme Valid?}
    B -- No --> C[Set used_image = False\nLog Warning]
    B -- Yes --> D[HTTP GET Request\nurllib3 Session Adapter]
    D --> E{Response Status}
    E -- 200 OK --> F[Read Bytes\nVerify with PIL.Image]
    E -- 404 / 403 / 500 --> G[Catch HTTPError\nLog Warning]
    E -- Connection Timeout > 3s --> H[Catch ConnectTimeout\nRetry 1x with backoff]
    E -- Read Timeout > 6s --> I[Catch ReadTimeout\nDrop Image]
    F --> J{Valid Image Bytes?}
    J -- Yes --> K[Process OpenCLIP Embedding\nLate Fusion 60/40]
    J -- Corrupt / Unrecognized --> L[Catch UnidentifiedImageError\nLog Warning]
    
    C --> M[Fallback to Text Classifier 100%\nApply Modality Multiplier 0.85x\nstatus = 'done']
    G --> M
    H --> M
    I --> M
    L --> M
    K --> N[Late Fusion Complete\nstatus = 'done']
```

### Key Fault Isolation Safeguards:
1. **Bounded Timeouts:** Bounded connect timeout (**3.0s**) and read timeout (**6.0s**) prevent network socket hangs.
2. **Explicit Exception Trapping:** `requests.exceptions.RequestException`, `urllib3.exceptions.HTTPError`, and `PIL.UnidentifiedImageError` are trapped individually.
3. **Graceful Text Fallback:** When image retrieval fails, the pipeline sets `used_image = False`, logs a warning, applies a $0.85\times$ text-only completeness multiplier, and marks the product `status = "done"`.
4. **Batch Continues Uninterrupted:** An image error on product $N$ has zero impact on product $N+1$.

---

## Question 9: API and Database Architecture

> **Question:**  
> *Explain the API and database architecture. Cover product import, classification, batch processing, status monitoring, results filtering, curation approvals, pagination, and data schemas.*

### Answer:

### 1. REST API Architecture (Django REST Framework)

| Method | Endpoint | Purpose | Query / Body Parameters | Response Status |
|---|---|---|---|---|
| `GET` | `/api/health/` | Health check & DB verification | None | `200 OK` |
| `GET` | `/api/products/` | Paginated catalog list | `?page=1&page_size=20&search=chair` | `200 OK` (DRF Page) |
| `POST` | `/api/imports/` | Upload catalog spreadsheet | `multipart/form-data` (`file`) | `201 Created` |
| `GET` | `/api/taxonomy/categories/` | Search taxonomy hierarchy | `?q=sofa&level=2&parent_id=...` | `200 OK` (Array) |
| `GET` | `/api/taxonomy/attributes/` | Category allowed attributes | `?category_id=gid://...` | `200 OK` (Array) |
| `POST` | `/api/jobs/` | Trigger batch classification | `{"batch_size": 5000}` | `201 Created` (`job_id`) |
| `GET` | `/api/jobs/{id}/` | Poll batch execution progress | None | `200 OK` (`progress_pct`) |
| `GET` | `/api/results/` | Filter classification results | `?needs_review=true&job_id=4` | `200 OK` (DRF Page) |
| `GET` | `/api/results/summary/` | Summary metrics & KPIs | `?job_id=4` | `200 OK` (Metrics JSON) |
| `PATCH` | `/api/results/{id}/` | Approve or override category | `{"approved": true, "category_id": "..."}` | `200 OK` (Detail JSON) |

### 2. Database Entities & Relationships
- **`Product`:** Stores raw supplier catalog fields, normalized image arrays, and quality scores.
- **`Category`:** Stores 14,606 Shopify taxonomy nodes with self-referencing `parent_id` hierarchy.
- **`Attribute` & `AttributeValue`:** Normalized allowed attributes and canonical values.
- **`ClassificationJob`:** Tracks batch metadata, total/processed counts, status, and execution duration.
- **`ClassificationResult`:** Stores predicted category, confidence, extracted attributes, alternatives, review flags, and curator approval state.

---

## Question 10: Optimizing 10,000 AI/API Requests

> **Question:**  
> *The scenario is: 10,000 products × ~2 seconds per external request. Explain why sequential processing is inefficient, calculate execution time, and explain optimization techniques (concurrency, async processing, connection reuse, vector caching, rate limits).*

### Answer:

### 1. Quantitative Latency Analysis

#### Sequential Execution (Inefficient Baseline):
- Products: $N = 10,000$
- Latency per product: $T_{\text{seq}} \approx 2.0\text{ seconds}$
- Total execution time:
  $$\text{Time}_{\text{sequential}} = 10,000 \times 2.0\text{ s} = 20,000\text{ s} \approx \mathbf{5.55\text{ hours}}$$

#### Optimized Concurrent Architecture:
With Celery worker concurrency $C = 20$, persistent HTTP connection pooling (`urllib3.PoolManager`), and pre-indexed vector dot products:
- Average latency per item: $T_{\text{opt}} \approx 0.20\text{ s}$
- Effective throughput:
  $$\text{Throughput} = \frac{C}{T_{\text{opt}}} = \frac{20}{0.20} = 100\text{ products/second}$$
- Total execution time:
  $$\text{Time}_{\text{optimized}} = \frac{10,000}{100} = 100\text{ seconds} \approx \mathbf{1.66\text{ minutes}}$$

### 2. Optimization Techniques Implemented:
1. **Pre-Indexed Category Vector Matrix:** Pre-computing all 14,606 category embeddings eliminates repeated transformer inference. Text classification takes only a single **15 ms NumPy matrix multiplication**.
2. **HTTP Connection Pooling:** `requests.Session` with `HTTPAdapter(pool_connections=20, pool_maxsize=50)` reuses TCP connections across image downloads.
3. **Controlled Concurrency:** Bounding worker processes ($N = 4\dots 8$ per node) prevents CPU/RAM thrashing or host CDN rate-limiting.

---

## Question 11: Resuming After Failure at 6,000 of 10,000 Products

> **Question:**  
> *Explain how the system resumes if processing stops after approximately 6,000 products of a 10,000 product batch. Cover persistent status, completed/failed/pending tracking, idempotency, and workflow to avoid reprocessing.*

### Answer:

```mermaid
sequenceDiagram
    participant User as Curator / Admin
    participant API as Django REST API
    participant DB as MariaDB
    participant BP as BatchProcessor (Worker)

    Note over DB: 6,000 products status='done'<br/>4,000 products pending
    User->>API: POST /api/jobs/ (or resume job #42)
    API->>BP: execute_batch(job_id=42)
    BP->>DB: Query completed product IDs:<br/>SELECT product_id FROM classification_results WHERE job_id=42 AND status='done'
    DB-->>BP: Return 6,000 IDs (set of done_product_ids)
    BP->>BP: Filter out done_product_ids from total catalog list
    Note over BP: Remaining to process = 4,000 items
    loop For each chunk of 100 in remaining 4,000 items
        BP->>BP: Classify 100 items
        BP->>DB: Bulk insert/update ClassificationResult
        BP->>DB: Update job.processed_products and progress_pct
    end
    BP->>DB: Update job.status = 'completed'
```

### Resumption Workflow:
1. **State Query:** Upon start/restart, `BatchProcessor` queries:
   ```python
   done_product_ids = set(
       ClassificationResult.objects.filter(job=job, status='done')
       .values_list('product_id', flat=True)
   )
   ```
2. **Skip Filter:** For each product in the catalog:
   ```python
   if product.id in done_product_ids:
       continue  # Skip already completed items
   ```
3. **Execution & Checkpointing:** Only the remaining 4,000 products are evaluated. Progress counters update from 6,000 to 10,000 with atomic commits every 5 items.
4. **Idempotency Guarantee:** Previously completed results and curator approvals are preserved without redundant computation.

---

## Question 12: Technology & Framework Choices

> **Question:**  
> *Explain the technology choices for this project (Python, Django, MariaDB, React, SentenceTransformers, OpenCLIP, RapidFuzz, Celery, Redis). Discuss problem fit, alternatives considered, and architectural trade-offs.*

### Answer:

| Technology | Selected For | Problems Solved | Alternatives Considered & Tradeoffs |
|---|---|---|---|
| **Python 3.12+** | Core Language | Rich ecosystem for scientific computing, NLP, and web services. | *Go / Node.js:* Faster raw execution, but lack mature ML ecosystems (`PyTorch`, `transformers`, `open-clip`). |
| **Django 5 & DRF** | Backend Framework | Robust ORM, built-in migrations, mature security model, standard REST serializer architecture. | *FastAPI:* Excellent async performance, but lacks comprehensive out-of-the-box admin, ORM migrations, and mature relational ecosystem. |
| **MariaDB / MySQL** | Primary Database | ACID compliance, robust foreign key constraints, efficient self-referencing hierarchy indexing for 14.6k categories. | *PostgreSQL:* Equally capable; MariaDB selected for native enterprise compatibility with host environment. *MongoDB:* Lacks strict relational constraints for hierarchical taxonomy trees. |
| **Sentence-Transformers** | Text Embeddings | High semantic accuracy for dense catalog search with compact 384-d vectors (`all-MiniLM-L6-v2`). | *OpenAI `text-embedding-3-small`:* High accuracy, but incurs ongoing API costs and network latency for 14.6k taxonomy embeddings. |
| **OpenCLIP (`ViT-B-32`)** | Visual Zero-Shot Classifier | Embeds images and text prompts into a joint space without requiring fine-tuning. | *ResNet / Custom CNN:* Requires extensive labeled training data for 14.6k classes; CLIP provides zero-shot categorization out of the box. |
| **RapidFuzz** | Fuzzy Lexical Matching | C++ accelerated fuzzy string similarity for high-throughput attribute extraction ($\approx 10\times$ faster than `fuzzywuzzy`). | *Regex only:* Fails on typos or slight spelling variants. *Fuzzywuzzy:* Pure Python implementation is too slow for batch pipelines. |
| **Celery + Redis** | Background Task Queue | Asynchronous job execution, chunk distribution, progress tracking, and worker fault isolation. | *Django-Q / Huey:* Lighter weight, but Celery offers superior production clustering, monitoring (Flower), and retry backoff policies. |
| **React 18 + Vite 5** | Frontend Dashboard | Fast HMR, reactive UI components, client-side routing, and accessible custom CSS design system. | *Next.js:* SSR overhead is unnecessary for an internal operational curation dashboard. |

---

## Question 13: High-Level System Architecture

> **Question:**  
> *Provide a clear high-level system architecture showing the complete data flow from product import to dashboard curation. Explain the responsibilities of each major component.*

### Answer:

```mermaid
graph TB
    subgraph Client Tier
        UI[React 18 Single Page Application\nDashboard, Review Workspace, Taxonomy Explorer]
    end

    subgraph API & Application Tier
        Nginx[Reverse Proxy / Static Server]
        Gunicorn[Django WSGI Application Server]
        DRF[Django REST Framework API Layer\nProducts, Taxonomy, Classification, Imports]
    end

    subgraph Async Processing Tier
        Redis[(Redis Message Broker)]
        CeleryWorker[Celery Batch Processing Workers\nChunk streaming, Retry adapters]
    end

    subgraph Machine Learning & Inference Tier
        ST[SentenceTransformers all-MiniLM-L6-v2\nDense Semantic Text Classifier]
        CLIP[OpenCLIP ViT-B-32\nZero-Shot Visual Classifier]
        Fuzz[RapidFuzz Attribute Extraction Engine]
        Cache[NumPy Pre-indexed Vector Matrix\n14,606 Category Vectors in RAM]
    end

    subgraph Persistence Tier
        DB[(MariaDB Database\nProducts, Taxonomy Tree, Attributes, Results, Jobs)]
    end

    UI <-->|HTTPS / REST API JSON| Nginx
    Nginx <--> Gunicorn
    Gunicorn <--> DRF
    DRF <--> DB
    DRF -->|Dispatch Batch Job| Redis
    Redis --> CeleryWorker
    CeleryWorker <--> ST
    CeleryWorker <--> CLIP
    CeleryWorker <--> Fuzz
    ST <--> Cache
    CeleryWorker <--> DB
```

### Component Responsibilities:
1. **Frontend Tier (`frontend/`):** Executive KPI metrics, live batch progress bars, catalog table, and curator review drawer with URL parameter synchronization.
2. **API Tier (`backend/config/`, `backend/products/`, etc.):** Input validation, pagination, authentication, and REST endpoints.
3. **Async Processing Tier (`backend/processing/`):** Background batch chunking (100 items), failure recovery, and database checkpointing.
4. **Machine Learning Tier (`backend/classification/engine/`):** Text embeddings, CLIP visual scoring, late fusion, and RapidFuzz attribute extraction.
5. **Persistence Tier (`MariaDB`):** Relational integrity across 14,606 categories, 8,240 attributes, products, and job execution logs.

---

## Question 14: Production Development Effort Estimation (Hours & WBS)

> **Question:**  
> *Provide a realistic production-ready development estimate in HOURS broken into individual tasks with assumptions, risks, dependencies, and total ranges.*

### Answer:

### 1. Work Breakdown Structure (WBS)

| # | Task / Deliverable | Senior Engineer (Hours) | QA / DevOps (Hours) | Total (Hours) | Assumptions & Technical Scope |
|---|---|:---:|:---:|:---:|---|
| 1 | **Requirements & Architecture Design** | 12 | 4 | **16** | System specifications, taxonomy schema design, API contract definition. |
| 2 | **Database Architecture & Migrations** | 10 | 4 | **14** | MariaDB models, self-referential hierarchy indexes, attribute relation schemas. |
| 3 | **Shopify Taxonomy Ingestion Engine** | 8 | 2 | **10** | JSON parser for 14,606 categories, 8,240 attributes, and 74,820 values. |
| 4 | **Product Catalog Ingestion (Excel/CSV)** | 12 | 4 | **16** | Multi-image column parser (up to 20 images), data quality metrics, bulk upserts. |
| 5 | **Dense Semantic Text Classifier** | 16 | 4 | **20** | SentenceTransformers pipeline, pre-indexed vector matrix, sub-20ms cosine dot product. |
| 6 | **Zero-Shot Visual Classifier (OpenCLIP)** | 18 | 6 | **24** | ViT-B-32 integration, prompt engineering, timeout/retry adapters for external CDNs. |
| 7 | **Late Fusion & Ranking Engine** | 10 | 4 | **14** | Weighted linear scoring ($0.60/0.40$), fallback logic, top-3 alternative candidate extraction. |
| 8 | **Category Attribute Extraction Engine** | 14 | 4 | **18** | RapidFuzz token matching, ancestor attribute inheritance, word-boundary regex parsing. |
| 9 | **Confidence Scoring & Review Rules** | 8 | 4 | **12** | Modality multipliers, ambiguity margin gap checks ($\Delta < 0.010$), low-info flags. |
| 10 | **Batch Processing & Celery Workers** | 16 | 6 | **22** | Redis broker setup, chunked execution (100 items), atomic checkpoints every 5 items. |
| 11 | **Resumability & Failure Recovery** | 10 | 4 | **14** | Skip logic for `done_product_ids`, idempotency safeguards, job restart workflows. |
| 12 | **Django REST Framework API Layer** | 14 | 6 | **20** | Pagination, filtering, summary KPI endpoint, 1-click curator PATCH endpoint. |
| 13 | **React 18 Curation Dashboard** | 24 | 8 | **32** | Review Workspace, specs drawer, KPI dashboard, live job polling, Dark/Light modes. |
| 14 | **Unit & Integration Test Suites** | 14 | 10 | **24** | 35+ backend tests (100% pass), API integration tests, parser edge case tests. |
| 15 | **Security, CI/CD & Production DevOps** | 10 | 10 | **20** | Docker Compose multi-service stack, GitHub Actions CI workflow, security headers. |
| 16 | **Technical Documentation & API Specs** | 10 | 2 | **12** | Architecture guides, API reference, deployment manuals, technical Q&A. |
| **Total** | **Full Production-Ready System** | **206 hrs** | **82 hrs** | **288 hrs (~7.2 engineering weeks)** |

### 2. Timeline Range & Risk Matrix
- **Realistic Timeline Range:** **260 – 320 Total Engineering Hours** (assuming a team of 1 Senior Full-Stack/ML Engineer and 1 QA/DevOps Engineer over 6–8 weeks).
- **Major Dependencies:** GPU compute availability (reduces CLIP inference latency from ~150ms to ~15ms per image), remote image CDN availability.
- **Risk Factors & Mitigation:**
  - *Data Sparsity:* Mitigated by low-information heuristics and routing to manual review.
  - *Processing Scale:* Mitigated by Celery concurrency, connection pooling, and pre-indexed embeddings.

---

## Current Prototype vs Production Architecture Comparison

| Component | Current Implementation | Production Scale Architecture | Rationale for Production Upgrade |
|---|---|---|---|
| **Vector Search** | In-memory NumPy cosine dot product against 14,606 vectors ($\approx 15\text{ ms}$). | Dedicated Vector Database (Milvus / Qdrant / pgvector) with HNSW indexing. | Enables scaling to millions of product vectors with sub-millisecond approximate nearest neighbor (ANN) retrieval. |
| **Model Serving** | Embedded in Celery worker processes via PyTorch CPU/GPU runtime. | Dedicated Model Serving Cluster (Triton / TorchServe / vLLM) behind gRPC. | Decouples web/worker memory from heavy deep-learning model weights and enables independent autoscaling. |
| **Image Pipeline** | Synchronous HTTP download inside worker with bounded timeouts (3s/6s) and retries. | Distributed Image Ingestion Pipeline: S3/GCS caching proxy with async worker pre-fetching. | Eliminates latency spikes from slow supplier image servers by staging images in local object storage prior to inference. |
| **Database** | Standalone MariaDB instance with InnoDB connection pooling. | MariaDB Galera Cluster or AWS Aurora MySQL with read replicas and Redis read-through caching. | Distributes read queries for high-concurrency multi-curator enterprise teams. |
| **Monitoring & Telemetry** | Python standard logging with file handlers + Celery job database status tracking. | OpenTelemetry + Prometheus + Grafana dashboards with Sentry error alerting. | Real-time observability into model drift, worker queue lag, and API endpoint p99 latencies. |
