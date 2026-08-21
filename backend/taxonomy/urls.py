from django.urls import path
from .views import CategoryListAPIView, CategoryDetailAPIView, AttributeListAPIView

app_name = 'taxonomy'

urlpatterns = [
    path('categories/', CategoryListAPIView.as_view(), name='category_list'),
    path('categories/<path:pk>/', CategoryDetailAPIView.as_view(), name='category_detail'),
    path('attributes/', AttributeListAPIView.as_view(), name='attribute_list'),
]
