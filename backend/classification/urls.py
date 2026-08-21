from django.urls import path
from .views import (
    ClassificationResultListAPIView,
    ClassificationResultSummaryAPIView,
    ClassificationResultDetailAPIView
)

app_name = 'classification'

urlpatterns = [
    path('results/', ClassificationResultListAPIView.as_view(), name='result_list'),
    path('results/summary/', ClassificationResultSummaryAPIView.as_view(), name='result_summary'),
    path('results/<int:pk>/', ClassificationResultDetailAPIView.as_view(), name='result_detail'),
]
