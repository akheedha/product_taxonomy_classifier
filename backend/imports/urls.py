from django.urls import path
from .views import ProductImportAPIView, CatalogImportHistoryAPIView

app_name = 'imports'

urlpatterns = [
    path('', CatalogImportHistoryAPIView.as_view(), name='import_history'),
    path('upload/', ProductImportAPIView.as_view(), name='import_upload'),
]
