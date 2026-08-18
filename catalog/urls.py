from django.urls import path
from .views import ProductImportAPIView

app_name = 'catalog'

urlpatterns = [
    path('import/', ProductImportAPIView.as_view(), name='product_import'),
]
