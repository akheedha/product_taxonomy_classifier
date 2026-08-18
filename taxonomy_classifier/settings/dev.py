"""
Development settings for taxonomy_classifier project.
Uses MariaDB/MySQL via environment variables and loads from .env.
"""

from .base import *  # noqa: F401, F403

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / '.env')  # noqa: F405
except ImportError:
    _env_file = BASE_DIR / '.env'  # noqa: F405
    if _env_file.exists():
        with open(_env_file, 'r', encoding='utf-8') as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith('#') and '=' in _line:
                    _k, _v = _line.split('=', 1)
                    os.environ[_k.strip()] = _v.strip()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-development-key-change-this-in-production-12345'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0').split(',')
    if host.strip()
]

# Database configuration for MariaDB / MySQL
# Environment variables: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT
DB_ENGINE = os.getenv('DB_ENGINE', 'django.db.backends.mysql')
DB_NAME = os.getenv('DB_NAME', 'taxonomy_classifier')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'rootpassword')
DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '3306')

db_options = {}
if 'mysql' in DB_ENGINE:
    db_options = {
        'charset': 'utf8mb4',
        'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
    }

DATABASES = {
    'default': {
        'ENGINE': DB_ENGINE,
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'OPTIONS': db_options,
    }
}

# Redis & Celery
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'django-db')
CELERY_CACHE_BACKEND = os.getenv('CELERY_CACHE_BACKEND', 'django-cache')

# In-memory email backend for dev
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS configuration for Vite dev origin (development only)
CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True
