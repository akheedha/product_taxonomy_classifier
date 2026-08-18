"""
URL configuration for taxonomy_classifier project.
"""

from django.contrib import admin
from django.urls import path, include
from .views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),

    # Classification & Review API routes: /api/jobs/, /api/results/
    path('api/', include('classification.urls', namespace='classification')),

    # Domain specific routes
    path('api/catalog/', include('catalog.urls', namespace='catalog')),
    path('api/taxonomy/', include('taxonomy.urls', namespace='taxonomy')),
]
