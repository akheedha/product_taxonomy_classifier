# Development Effort & Estimation Documentation

## 1. Project Scope & Architecture Summary
This project delivers a multi-modal product categorization platform integrating Shopify's 14,606 taxonomy categories with Sentence-Transformers and OpenCLIP, background Celery workers, and a modern React curation dashboard.

---

## 2. Work Breakdown Structure (WBS) & Effort Estimation

| Phase / Feature Area | Task Breakdown | Senior Dev (Hours) | QA / DevOps (Hours) | Total (Hours) |
|---|---|:---:|:---:|:---:|
| **1. Data Modeling & Ingestion** | • MariaDB Schema Design (Products, Taxonomy, Imports, Jobs, Results)<br>• Resilient Excel/CSV Parser with 20-image column aggregation<br>• Bulk upsert optimizations and data quality audit reporting | 14 | 4 | **18** |
| **2. Taxonomy Integration** | • Shopify Taxonomy JSON ingestion command (14,606 nodes)<br>• Breadcrumb hierarchy algorithms (`get_ancestors`)<br>• Full-text search and attribute mapping services | 10 | 3 | **13** |
| **3. Multi-Modal AI Engine** | • Sentence-Transformers semantic text embedding pipeline<br>• OpenCLIP zero-shot visual similarity classifier<br>• Late fusion weighting and RapidFuzz attribute extractor<br>• Confidence calibration, margin gap checks & review heuristics | 24 | 8 | **32** |
| **4. Processing & Scalability** | • Celery + Redis background chunk worker configuration<br>• Resumable state persistence (skip completed items on restart)<br>• Per-product fault isolation and live progress checkpointing | 16 | 6 | **22** |
| **5. REST API Services** | • Thin DRF controllers, serializers, and service layer<br>• Filtering, search, summary metrics, and in-place approvals | 12 | 4 | **16** |
| **6. Frontend Curation UI** | • React 18 + Vite client-side routed architecture (4 pages)<br>• Executive dashboard, KPI cards, real-time job pulse<br>• Curator review workspace with drawer expansion & URL syncing<br>• Interactive taxonomy tree & attribute schema explorer | 22 | 6 | **28** |
| **7. Testing & Quality Assurance** | • 35+ Unit & integration test suites across all domains<br>• End-to-end browser verification and error handling checks | 12 | 8 | **20** |
| **8. CI/CD & Production DevOps** | • Docker Compose stack (Django, MariaDB, Redis, Celery, React)<br>• GitHub Actions CI workflow with automated test runs<br>• Production settings, security headers, and documentation | 8 | 6 | **14** |
| **Total Effort** | **Full End-to-End Implementation** | **118 hrs** | **45 hrs** | **163 hrs (~4 weeks)** |

---

## 3. Key Assumptions & Risk Matrix

### Assumptions
1. **Infrastructure:** MariaDB 11.4+ and Redis 7+ available locally or via Docker.
2. **Compute:** CPU-based inference for SentenceTransformers and OpenCLIP performs at ~15-25ms per item; GPU acceleration reduces latency to <5ms per item.
3. **Data Quality:** Supplier catalog spreadsheets provide at least a unique SKU/Product Number.

### Risk Mitigation Strategies
- **High Concurrency / Large Catalogs (10,000+ items):** Processed in chunks of 100 with periodic database commits. Individual product errors are caught and recorded without aborting the batch.
- **External Image 404s:** Fallback to text semantic classification with calibrated confidence penalties.
