"""
Core views for taxonomy_classifier project, including health check.
"""

import time
from django.db import connection
from django.http import JsonResponse
from django.conf import settings


def health_check(request):
    """
    Health check endpoint at /api/health/
    Returns service health status, DB connectivity check, and timestamp.
    """
    start_time = time.time()
    db_status = "unknown"
    db_error = None

    try:
        connection.ensure_connection()
        db_status = "connected"
    except Exception as e:
        db_status = "disconnected"
        db_error = str(e)

    duration_ms = round((time.time() - start_time) * 1000, 2)

    is_healthy = db_status == "connected"

    response_data = {
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "taxonomy_classifier",
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production",
        "checks": {
            "database": {
                "status": db_status,
                "engine": settings.DATABASES["default"]["ENGINE"],
                "host": settings.DATABASES["default"].get("HOST", "127.0.0.1"),
                "name": settings.DATABASES["default"].get("NAME", ""),
                "error": db_error,
            }
        },
        "response_time_ms": duration_ms,
    }

    # Return 200 if healthy, 503 if database connection fails
    status_code = 200 if is_healthy else 503
    return JsonResponse(response_data, status=status_code)
