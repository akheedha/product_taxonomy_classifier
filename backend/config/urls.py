"""
Root URL configuration for product_taxonomy_classifier platform.
"""

from django.contrib import admin
from django.urls import path, include
from common.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health/', health_check, name='health_check'),

    # Modular Domain APIs
    path('api/products/', include('products.urls', namespace='products')),
    path('api/imports/', include('imports.urls', namespace='imports')),
    path('api/catalog/', include('imports.urls', namespace='catalog_legacy')),  # legacy compatibility
    path('api/taxonomy/', include('taxonomy.urls', namespace='taxonomy')),
    path('api/', include('classification.urls', namespace='classification')),
    path('api/', include('processing.urls', namespace='processing')),
]
