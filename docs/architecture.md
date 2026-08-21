# System Architecture & Design Documentation

## 1. High-Level Overview

The **Shopify Product Taxonomy Classifier & Curator Platform** is an enterprise-grade solution designed to ingest raw vendor product catalogs (spreadsheets), normalize product data, classify items into the official Shopify Product Taxonomy (14,606 nodes) using multi-modal AI, and provide a human-in-the-loop review dashboard.

```
┌────────────────────────────────────────────────────────────────────────┐
│                              REACT SPA                                 │
│  [DashboardPage]    [ReviewPage]    [ImportPage]    [TaxonomyPage]     │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / REST
┌───────────────────────────────────▼────────────────────────────────────┐
│                        DJANGO 5 REST FRAMEWORK                         │
│                                                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   products   │  │   imports    │  │   taxonomy   │  │ processing │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  └─────┬──────┘  │
│                                                              │         │
│  ┌────────────────────────────────────────────────────────┐  │         │
│  │               classification (ML Engine)               │  │         │
│  │  [TextClassifier]   [ImageClassifier]   [Fusion]      │  │         │
│  └────────────────────────────────────────────────────────┘  │         │
└──────────────────┬───────────────────────────────────────────┼─────────┘
                   │                                           │
       ┌───────────▼──────────┐                   ┌────────────▼──────────┐
       │   MariaDB Database   │                   │  Celery + Redis Broker │
       └──────────────────────┘                   └───────────────────────┘
```

---

## 2. Modular Domain Architecture

### `products` Domain
- **Role:** Pure catalog entity management and persistence.
- **Components:**
  - `models.Product`: Core model with attributes, dimensions, pricing, and JSON image arrays.
  - `services.ProductService`: Filtering, SKU lookup, and catalog mutations.
  - `views.ProductListAPIView` / `ProductDetailAPIView`: REST endpoints for product records.

### `imports` Domain
- **Role:** File ingestion, spreadsheet parsing, validation, and data quality logging.
- **Components:**
  - `excel_parser.ExcelCatalogParser`: Parses `.xlsx`, `.xls`, `.csv` spreadsheets; aggregates multi-image columns (`Image 1` ... `Image 20`).
  - `validators.validate_product_row`: Schema verification and missing SKU handling.
  - `models.CatalogImport`: Audit log tracking row counts, skipped items, and quality metrics.
  - `services.ImportService`: High-performance bulk database upserts (`bulk_create` / `bulk_update`).

### `taxonomy` Domain
- **Role:** Shopify Product Taxonomy storage and hierarchy queries.
- **Components:**
  - `models.Category`: Hierarchical tree model with `get_ancestors()` and depth levels.
  - `models.Attribute` & `AttributeValue`: Category-mapped attribute definitions and allowed values.
  - `services.TaxonomyService`: Real-time category search and attribute retrieval.

### `classification` Domain
- **Role:** Multi-modal AI intelligence and curator review outcomes.
- **Components:**
  - `engine/text_classifier.py`: Sentence-Transformers semantic text embeddings & RapidFuzz ranking.
  - `engine/image_classifier.py`: OpenCLIP ViT-B-32 zero-shot visual similarity.
  - `engine/attribute_extractor.py`: Rule-based & regex attribute parser.
  - `engine/fusion.py`: Late fusion combining text (60%) and image (40%) signals.
  - `confidence.py`: Calibrated confidence calculation, margin gap checks, and human review reasoning.
  - `models.ClassificationResult`: Persisted classification outcomes with curator approval/override flags.

### `processing` Domain
- **Role:** Background job management, batch chunking, fault isolation, and resumability.
- **Components:**
  - `models.ClassificationJob`: Batch execution tracker (total, processed, failed, timing).
  - `batch_processor.BatchProcessor`: Chunked processing with atomic checkpoints every 5 items.
  - `tasks.process_classification_job`: Asynchronous Celery worker task.
  - `retry.py`: Exponential backoff and fault tolerance decorators.

### `common` Infrastructure
- **Role:** System-wide constants, custom exceptions, HTTP connection pooling, and health check endpoints.

---

## 3. Fault Tolerance & Resumability

1. **Item-Level Fault Isolation:** An individual image download error or classification exception is caught and recorded as `status='failed'` on the `ClassificationResult` without crashing or aborting the batch job.
2. **Resumable Execution:** If a worker process is interrupted after processing 6,000 of 10,000 items, restarting the job skips all records already marked `status='done'`.
3. **Database Checkpointing:** Progress counters are committed frequently to MariaDB, allowing the frontend to poll and render smooth progress bars in real-time.
