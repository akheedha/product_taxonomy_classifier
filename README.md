# Product Taxonomy Classifier & Curator Platform

A Django 5 machine-learning powered service designed to classify e-commerce product catalogs into standardized taxonomy (such as Shopify category trees & attributes) and execute classification jobs asynchronously using Celery and Redis.

> 📖 **Candidate Answers & Architecture Whitepaper**: Detailed answers to Questions 1 through 14 from the technical assessment are provided in [ANSWERS.md](file:///d:/assignment/product_taxonomy_classifier/ANSWERS.md).

---

## 📁 Architecture & Apps

The project is structured into modular domain apps:

- **`catalog`**: Product data models, raw catalog storage, and batch product import handlers (CSV/XLSX/JSON).
- **`taxonomy`**: Shopify taxonomy schemas, hierarchical category trees, attributes, and allowed attribute values.
- **`classification`**: Classification execution engine (sentence embeddings, multi-modal CLIP, string matching), async job coordinator, and classification result logging.
- **`taxonomy_classifier`**: Project root configuration, split settings (`base`, `dev`, `prod`), Celery setup, root routing, and health checks.
- **`frontend`**: Modern React + Vite curator dashboard for reviewing, filtering, approving, and manually overriding classifications.


---

## 🛠️ Tech Stack & Dependencies

- **Framework**: Django 5.x, Django REST Framework
- **Database**: MariaDB 11.x (via `mysqlclient` / `mariadb`)
- **Queue / Broker**: Celery 5.x, Redis 7.x, `django-celery-results`
- **Machine Learning & NLP**: PyTorch, `sentence-transformers`, `open-clip-torch`, `rapidfuzz`
- **Data & Media**: `pandas`, `openpyxl`, `Pillow`, `requests`
- **Configuration**: `python-dotenv`

---

## 🚀 Getting Started (Local Development)

### 1. Prerequisites

- Python 3.10+ (tested on Python 3.13)
- Docker & Docker Compose (for MariaDB & Redis)
- C/C++ build tools / MySQL development libraries (if compiling `mysqlclient` on Windows/Linux)

---

### 2. Clone and Setup Virtual Environment

```bash
# Navigate to the workspace
cd /path/to/product_taxonomy_classifier

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Windows (CMD):
.\venv\Scripts\activate.bat
# On Linux / macOS:
source venv/bin/activate
```

---

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 4. Configure Environment Variables

Copy the sample environment file to `.env`:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux / macOS
cp .env.example .env
```

Review and update `.env` if your local ports or passwords differ:

| Variable | Default Value | Description |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `taxonomy_classifier.settings.dev` | Active Django settings module |
| `SECRET_KEY` | `...` | Django cryptographic signing key |
| `DEBUG` | `True` | Enable debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1,0.0.0.0` | Allowed HTTP host headers |
| `DB_ENGINE` | `django.db.backends.mysql` | Django database backend |
| `DB_NAME` | `taxonomy_classifier` | MariaDB database name |
| `DB_USER` | `root` | MariaDB username |
| `DB_PASSWORD` | `rootpassword` | MariaDB password |
| `DB_HOST` | `127.0.0.1` | MariaDB host address |
| `DB_PORT` | `3306` | MariaDB port |
| `REDIS_URL` | `redis://127.0.0.1:6379/0` | Redis instance URL |
| `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/0` | Celery broker URL |
| `CELERY_RESULT_BACKEND` | `django-db` | Store task results in database |

---

### 5. Start MariaDB and Redis Containers

Run Docker Compose to spin up local database and cache services:

```bash
docker compose up -d
```

Verify that services are running and healthy:

```bash
docker compose ps
```

---

### 6. Run Database Migrations

Apply Django core and third-party migrations (including `django_celery_results`):

```bash
python manage.py migrate
```

---

### 7. Create Superuser (Admin Access)

```bash
python manage.py createsuperuser
```

---

### 8. Import Shopify Taxonomy & Catalog Data

```bash
# 1. Download and ingest official Shopify category trees & attributes (5,000+ nodes)
python manage.py import_taxonomy

# 2. Ingest sample product catalog spreadsheet (.xlsx or .csv)
python manage.py import_products "data/Product List.xlsx"

# 3. (Optional) Run classification batch job via CLI
python manage.py run_classification_job --batch-size=100
```

---

### 9. Start Background Celery Worker

In a separate terminal window (with the virtual environment activated):

```bash
# On Linux / macOS:
celery -A taxonomy_classifier worker -l info

# On Windows:
celery -A taxonomy_classifier worker -l info --pool=solo
```

---

### 10. Start the Development Web Server

```bash
python manage.py runserver 0.0.0.0:8000
```

---

### 11. Start the React + Vite Review Frontend

In a separate terminal window:

```bash
cd frontend
npm install
npm run dev
```

Open your browser at **`http://localhost:5173/`** to access the **Shopify Product Taxonomy Classifier & Curator Review Dashboard**.

---

### 12. Run Automated Test Suites

```bash
# Run Django test suite (30 unit & integration test cases)
python manage.py test
```

---

## 🔍 Health Check & Verification

Once the development server is running, you can test the system health endpoint:

```bash
curl http://127.0.0.1:8000/api/health/
```

Expected JSON Response (`HTTP 200 OK`):

```json
{
  "status": "healthy",
  "service": "taxonomy_classifier",
  "version": "1.0.0",
  "environment": "development",
  "checks": {
    "database": {
      "status": "connected",
      "engine": "django.db.backends.mysql",
      "host": "127.0.0.1",
      "name": "taxonomy_classifier",
      "error": null
    }
  },
  "response_time_ms": 12.4
}
```

---

## 📂 Project Directory Layout

```
.
├── .env.example                   # Example environment configuration
├── .gitignore                      # Git ignore patterns
├── docker-compose.yml              # Local MariaDB + Redis stack
├── requirements.txt                # Pinned dependencies
├── manage.py                       # Django CLI entrypoint
├── README.md                       # Local runbook & documentation
├── frontend/                       # React + Vite curator review dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
├── catalog/                        # Product catalog & import app
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── taxonomy/                       # Shopify category/attribute taxonomy app
│   ├── apps.py
│   ├── models.py
│   ├── urls.py
│   └── views.py
├── classification/                 # Classification jobs & engine app
│   ├── apps.py
│   ├── models.py
│   ├── tasks.py                    # Async Celery tasks
│   ├── urls.py
│   └── views.py
└── taxonomy_classifier/            # Project configuration
    ├── asgi.py
    ├── celery.py                   # Celery application instance
    ├── urls.py                     # Root routing
    ├── views.py                    # Health check endpoint
    ├── wsgi.py
    └── settings/
        ├── __init__.py
        ├── base.py                 # Common configuration
        ├── dev.py                  # Dev settings (MariaDB + Redis from .env)
        └── prod.py                 # Production settings
```
