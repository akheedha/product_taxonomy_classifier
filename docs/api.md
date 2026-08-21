# REST API Specification

Base URL: `http://localhost:8000/api`

---

## 1. System Health
### `GET /api/health/`
Checks database connectivity and server latency.
- **Response `200 OK`:**
  ```json
  {
    "status": "healthy",
    "service": "product_taxonomy_classifier",
    "version": "1.0.0",
    "checks": {
      "database": {
        "status": "connected",
        "engine": "django.db.backends.mysql",
        "name": "taxonomy_classifier",
        "error": null
      }
    },
    "response_time_ms": 2.45
  }
  ```

---

## 2. Products (`/api/products/`)
### `GET /api/products/`
List products with filtering and pagination.
- **Query Params:** `search`, `category`, `brand`, `page`, `page_size`
- **Response `200 OK`:**
  ```json
  {
    "count": 1000,
    "next": "http://localhost:8000/api/products/?page=2",
    "previous": null,
    "results": [
      {
        "id": 1,
        "product_number": "SKU-1001",
        "product_name": "Modern Velvet Accent Chair",
        "brand": "Nordic Craft",
        "product_category": "Furniture",
        "product_sub_category": "Chairs",
        "materials": "Velvet, Solid Oak",
        "product_color": "Navy Blue",
        "primary_image": "https://example.com/img1.jpg",
        "images": ["https://example.com/img1.jpg", "https://example.com/img2.jpg"]
      }
    ]
  }
  ```

### `GET /api/products/{id}/`
Retrieve full product details.

---

## 3. Catalog Ingestion (`/api/imports/`)
### `POST /api/imports/upload/`
Upload and ingest raw product spreadsheets (`.xlsx`, `.xls`, `.csv`).
- **Content-Type:** `multipart/form-data`
- **Payload:** `file` (File), `sheet` (optional string/int, default 0), `batch_size` (optional int)
- **Response `201 Created`:**
  ```json
  {
    "detail": "Product catalog imported successfully.",
    "filename": "supplier_catalog.xlsx",
    "result": {
      "import_id": 4,
      "filename": "supplier_catalog.xlsx",
      "status": "success",
      "total_rows": 1000,
      "imported_count": 1000,
      "skipped_count": 0,
      "data_quality_metrics": {
        "total_rows_in_file": 1000,
        "valid_records_parsed": 1000,
        "missing_description_count": 42,
        "missing_images_count": 15
      },
      "elapsed_seconds": 3.82
    }
  }
  ```

---

## 4. Taxonomy Exploration (`/api/taxonomy/`)
### `GET /api/taxonomy/categories/`
Search Shopify category tree.
- **Query Params:** `q` (search string), `level` (depth), `parent` (parent ID)
- **Response `200 OK`:**
  ```json
  [
    {
      "id": "gid://shopify/TaxonomyCategory/fr-22",
      "name": "Sofas",
      "full_name": "Furniture > Seating > Sofas",
      "level": 2,
      "parent": "gid://shopify/TaxonomyCategory/fr-2"
    }
  ]
  ```

### `GET /api/taxonomy/attributes/?category={category_id}`
Retrieve attributes and allowed values mapped to a category.

---

## 5. Classification & Curation (`/api/results/`)
### `GET /api/results/`
Paginated, filtered list of classified products.
- **Query Params:** `job`, `needs_review` (bool), `approved` (bool), `min_conf` (float), `max_conf` (float), `search`, `category`, `page`

### `GET /api/results/summary/`
Retrieve aggregate KPI metrics for executive cards.
- **Query Params:** `job` (optional)
- **Response `200 OK`:**
  ```json
  {
    "total_results": 1000,
    "approved_count": 820,
    "needs_review_count": 180,
    "failed_count": 0,
    "average_confidence": 0.842,
    "approval_rate_percent": 82.0,
    "review_rate_percent": 18.0
  }
  ```

### `PATCH /api/results/{id}/`
Approve or override category for a classified product.
- **Payload:**
  ```json
  {
    "approved": true,
    "category_id": "gid://shopify/TaxonomyCategory/fr-22",
    "reviewed_by": "curator_name"
  }
  ```

---

## 6. Batch Processing (`/api/jobs/`)
### `POST /api/jobs/`
Create and queue a batch classification job.
- **Payload:** `{"limit": 0, "sync": false}`
- **Response `201 Created`:**
  ```json
  {
    "id": 5,
    "status": "pending",
    "progress_percentage": 0.0,
    "total_products": 1000,
    "processed_count": 0,
    "failed_count": 0,
    "created_at": "2026-08-20T23:30:00Z"
  }
  ```

### `GET /api/jobs/{id}/`
Poll job progress and timing in real time.

### `POST /api/jobs/{id}/resume/`
Resume an interrupted or partial batch job.
