# Shopify Product Taxonomy Classifier & Curator Platform

[![CI Pipeline](https://github.com/organization/product_taxonomy_classifier/actions/workflows/ci.yml/badge.svg)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green.svg)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Vite-5.0-646cff.svg)](https://vitejs.dev/)
[![MariaDB](https://img.shields.io/badge/MariaDB-11.4-brown.svg)](https://mariadb.org/)
[![Redis](https://img.shields.io/badge/Redis-7.0-red.svg)](https://redis.io/)

An enterprise-grade, multi-modal automated product categorization and human curation platform. Ingests raw supplier catalog spreadsheets, aggregates multi-image arrays and attributes, automatically maps products to the official **Shopify Product Taxonomy (14,606 hierarchical categories)** using **Sentence-Transformers** and **OpenCLIP**, extracts category-specific attributes using **RapidFuzz**, and provides a full-featured curation workspace for catalog operations.

> [!IMPORTANT]
> 📖 **Technical Architecture & Design Questions:** The complete answers to all 14 technical design and architectural questions are available directly in [**QUESTIONS.md**](QUESTIONS.md).

---

## 📑 Table of Contents
1. [Technical Architecture Q&A (QUESTIONS.md)](#-technical-architecture-qa)
2. [Project Overview](#1-project-overview)
3. [Key Features](#2-key-features)
4. [Architecture & Domain Boundaries](#3-architecture--domain-boundaries)
5. [Technology Stack](#4-technology-stack)
6. [Directory Structure](#5-directory-structure)
7. [Setup Instructions](#6-setup-instructions)
8. [Environment Variables](#7-environment-variables)
9. [Database Setup](#8-database-setup)
10. [Running the Backend](#9-running-the-backend)
11. [Running the Frontend](#10-running-the-frontend)
12. [Running Celery & Redis](#11-running-celery--redis)
13. [Excel / CSV Upload Format](#12-excel--csv-upload-format)
14. [Multi-Modal Classification Pipeline](#13-multi-modal-classification-pipeline)
15. [Confidence Scoring & Review Triggers](#14-confidence-scoring--review-triggers)
16. [Batch Processing & Scalability](#15-batch-processing--scalability)
17. [Failure Recovery & Resumability](#16-failure-recovery--resumability)
18. [REST API Endpoints](#17-rest-api-endpoints)
19. [Testing & Quality Assurance](#18-testing--quality-assurance)
20. [Documentation Index](#19-documentation-index)

---

## 📖 Technical Architecture Q&A

For complete, technically grounded answers to the 14 core system design questions, see [**QUESTIONS.md**](QUESTIONS.md):

- **Q1:** Automatic Shopify Category, Attributes & Attribute Values Identification
- **Q2:** Handling Products With Title but No Description or Image
- **Q3:** Using Product Images for Visual Categorization (`OpenCLIP ViT-B-32`)
- **Q4:** Large-Scale Processing of 10,000+ Products (Celery & Redis)
- **Q5:** Shopify Taxonomy Database Structure & Hierarchy (MariaDB)
- **Q6:** Determining Classification Confidence Score & Calibrated Thresholds
- **Q7:** Handling Uncertain or Multiple Category Results & Curator Overrides
- **Q8:** Broken or Inaccessible Image Handling & Fault Isolation
- **Q9:** API and Database Architecture (DRF & Relational ERD)
- **Q10:** Optimizing 10,000 AI/API Requests (Latency Analysis & Concurrency)
- **Q11:** Failure Recovery & Resumption After 6,000 Products
- **Q12:** Technology & Framework Choices (Django, MariaDB, React, PyTorch)
- **Q13:** High-Level System Architecture & Context Diagram
- **Q14:** Production Development Effort Estimation (288 Hours, 16 Tasks WBS)
- **PROD:** Current Prototype vs Production Architecture Comparison

---

## 1. Project Overview
E-commerce merchants frequently receive raw vendor catalogs with inconsistent categorizations, missing descriptions, or unstandardized attributes. This platform automates the transformation of unstructured catalog data into canonical Shopify Taxonomy standards while flagging ambiguous or low-confidence predictions for human curation.

---

## 2. Key Features
- **Multi-Modal AI Pipeline:** Combines dense semantic text embeddings (`all-MiniLM-L6-v2`) with zero-shot visual similarity (`OpenCLIP ViT-B-32`).
- **Resilient Spreadsheet Ingestion:** Parses `.xlsx`, `.xls`, and `.csv` files, aggregating up to 20 images per product and generating data quality reports.
- **Shopify Taxonomy Explorer:** Fast search across 14,606 category hierarchy nodes and mapped allowed attribute schemas.
- **Curator Review Workspace:** Distraction-free review table with URL parameter synchronization (`?job=`, `?needs_review=`, `?min_conf=`), expandable metadata drawers, 1-click approvals, and alternative category overrides.
- **Fault-Tolerant Batch Processing:** Background Celery workers with 100-item chunking, per-item fault isolation, and resumable execution state.

---

## 3. Architecture & Domain Boundaries
The backend is structured into clean modular domain applications:

```text
backend/
├── config/          # Core Django settings, URLs, Celery, and WSGI/ASGI gateways
├── products/        # Product catalog models, persistence, and CRUD services
├── imports/         # Excel/CSV parser, row validators, and upload API
├── taxonomy/        # Shopify category hierarchy, attributes, and search services
├── classification/  # Multi-modal ML engine (text, image, fusion) & confidence logic
├── processing/      # Background Celery tasks, batch processor, retry & resumption
└── common/          # Shared constants, custom exceptions, and health checks
```

For complete architectural diagrams and design rationales, see [docs/architecture.md](docs/architecture.md) and [docs/technical-design.md](docs/technical-design.md).

---

## 4. Technology Stack
- **Backend:** Python 3.12+, Django 5, Django REST Framework, Celery, Pandas, PyTorch, OpenCLIP, Sentence-Transformers, RapidFuzz.
- **Database & Cache:** MariaDB 11.4+ (`utf8mb4`), Redis 7.
- **Frontend:** React 18, Vite 5, React Router v6, custom accessible CSS design system with Dark/Light modes.

---

## 5. Directory Structure
```text
product_taxonomy_classifier/
├── QUESTIONS.md             # Master technical design questions & answers
├── README.md                # Project documentation & quickstart guide
├── docker-compose.yml       # Local MariaDB & Redis services
├── .env.example             # Environment configuration template
├── .gitignore
├── backend/
│   ├── config/              # Django settings (base, development, production), celery, urls
│   ├── products/            # Product models, serializers, views, services, tests
│   ├── imports/             # Excel parser, validators, services, views, tests
│   ├── taxonomy/            # Category & Attribute models, import command, tests
│   ├── classification/      # ML engine (fusion, text, image, attributes), confidence
│   ├── processing/          # Celery tasks, batch processor, retry policies, tests
│   ├── common/              # Constants, exceptions, health check view
│   ├── scripts/             # Standalone review analysis and diagnostic scripts
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/      # common/, results/, imports/, taxonomy/
│   │   ├── pages/           # DashboardPage, ReviewPage, ImportPage, TaxonomyPage
│   │   ├── services/        # api.js, products.js, imports.js, classification.js, taxonomy.js
│   │   ├── hooks/           # usePolling.js
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── docs/                    # technical-design.md, architecture.md, api.md, etc.
└── .github/workflows/       # ci.yml GitHub Actions pipeline
```

---

## 6. Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 20+ & npm
- MariaDB 11.4+ (or Docker)
- Redis 7+ (or Docker)

---

## 7. Environment Variables
Create `backend/.env` based on `backend/.env.example`:

```ini
DEBUG=True
SECRET_KEY=development-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,testserver

DB_ENGINE=django.db.backends.mysql
DB_NAME=taxonomy_classifier
DB_USER=root
DB_PASSWORD=rootpassword
DB_HOST=127.0.0.1
DB_PORT=3306

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
```

---

## 8. Database Setup
Start MariaDB and Redis using Docker:
```bash
docker compose up -d
```

Run database migrations and import the full Shopify Taxonomy:
```bash
cd backend
python manage.py migrate
python manage.py import_taxonomy
```

---

## 9. Running the Backend
```bash
cd backend
python manage.py runserver 127.0.0.1:8000
```
Backend API will be accessible at: `http://127.0.0.1:8000/api/`

---

## 10. Running the Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend UI will be accessible at: `http://localhost:5173/`

---

## 11. Running Celery & Redis
Start Celery worker for asynchronous batch processing:
```bash
cd backend
celery -A config worker --loglevel=info -P solo
```

---

## 12. Excel / CSV Upload Format
Supported formats: `.xlsx`, `.xls`, `.xlsm`, `.csv`. The parser detects standard headers:
- `Product Number` or `SKU`: Mandatory unique identifier.
- `Product Name` or `Title`: Product name.
- `Brand`, `Vendor`, or `Manufacturer`: Brand name.
- `Product Description` / `Bullets`: Detailed marketing copy.
- `Product Category` / `Product Sub Category`: Source category breadcrumb.
- `Product Color` / `Materials`: Physical specifications.
- `Image 1` ... `Image 20`: Aggregated into primary and secondary images.

---

## 13. Multi-Modal Classification Pipeline
- **Dense Text Embeddings (60% weight):** Sentence-Transformers encodes product title, brand, description, and source categories into dense 384-d vectors matched against pre-indexed Shopify taxonomy vectors.
- **Zero-Shot Visual Similarity (40% weight):** OpenCLIP ViT-B-32 evaluates visual similarity against natural category prompts for the top text candidates.
- **Late Fusion:** Weighted linear combination generates final candidate scores.
- **Attribute Extraction:** RapidFuzz token matching & word-boundary regex match allowed category attributes and values.

---

## 14. Confidence Scoring & Review Triggers
Predictions are automatically routed to the Curator Review Queue if:
1. **Low Confidence:** Score is below threshold (`< 0.55`).
2. **Sibling Ambiguity:** Difference between Rank 1 and Rank 2 score is `< 0.01` (with top score `< 0.65`).
3. **Low Information:** Missing marketing description or sparse product record.
4. **Image Failure:** Image download fails or URL is inaccessible.

---

## 15. Batch Processing & Scalability
- **Chunking:** Ingests and processes products in chunks of 100 items.
- **Atomic Checkpoints:** Commits progress every 5 items for live UI progress updates.
- **Fault Isolation:** A failed item does not abort the batch job.
- **Pre-Computed Embeddings:** Category vector dot product runs in **12–18 ms** per product.

---

## 16. Failure Recovery & Resumability
If a 10,000-item batch job is interrupted at item 6,000, resuming the job queries completed products and processes only the remaining 4,000 items without redundant computation:
```bash
python manage.py run_classification_job --resume=1
```

---

## 17. REST API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health/` | Service health check & DB latency |
| `GET` | `/api/products/` | Paginated product list with search filters |
| `POST` | `/api/imports/` | Upload and parse catalog spreadsheet (.xlsx, .csv) |
| `GET` | `/api/taxonomy/categories/` | Search Shopify taxonomy tree (14,606 nodes) |
| `GET` | `/api/taxonomy/attributes/` | List allowed attributes for category |
| `GET` | `/api/results/` | Paginated classification results |
| `GET` | `/api/results/summary/` | Aggregate KPI statistics |
| `PATCH` | `/api/results/{id}/` | Approve or override category |
| `POST` | `/api/jobs/` | Queue batch classification job |
| `GET` | `/api/jobs/{id}/` | Poll batch job progress |

---

## 18. Testing & Quality Assurance
Run backend test suites:
```bash
cd backend
python manage.py test
```

Build frontend production bundle:
```bash
cd frontend
npm run build
```

---

## 19. Documentation Index
- [**QUESTIONS.md**](QUESTIONS.md) — Master technical design questions and comprehensive answers.
- [**docs/technical-design.md**](docs/technical-design.md) — Complete technical design and architecture guide.
- [**docs/architecture.md**](docs/architecture.md) — Domain boundaries and system architecture.
- [**docs/api.md**](docs/api.md) — Complete REST API reference and request/response schemas.
- [**docs/classification-approach.md**](docs/classification-approach.md) — ML embedding and multimodal fusion details.
- [**docs/development-estimation.md**](docs/development-estimation.md) — Work breakdown structure and production effort estimates.
