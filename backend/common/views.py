"""
Common system views such as health check.
"""

import time
from django.db import connection
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """
    Service health check endpoint verifying database connectivity and latency.
    """
    start_time = time.time()
    db_status = "connected"
    db_error = None

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:
        db_status = "error"
        db_error = str(exc)

    response_time = round((time.time() - start_time) * 1000, 2)
    is_healthy = db_status == "connected"

    return Response({
        "status": "healthy" if is_healthy else "unhealthy",
        "service": "product_taxonomy_classifier",
        "version": "1.0.0",
        "checks": {
            "database": {
                "status": db_status,
                "engine": connection.settings_dict.get('ENGINE'),
                "name": connection.settings_dict.get('NAME'),
                "error": db_error,
            }
        },
        "response_time_ms": response_time
    }, status=200 if is_healthy else 503)
