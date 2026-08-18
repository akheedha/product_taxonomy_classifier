from django.urls import path
from .api import (
    JobListCreateAPIView,
    JobDetailAPIView,
    ResultListAPIView,
    ResultSummaryAPIView,
    ResultDetailUpdateAPIView,
)

app_name = 'classification'

urlpatterns = [
    # Job endpoints: /api/jobs/ and /api/jobs/{id}/
    path('jobs/', JobListCreateAPIView.as_view(), name='job_list_create'),
    path('jobs/<int:pk>/', JobDetailAPIView.as_view(), name='job_detail'),

    # Result endpoints: /api/results/ and /api/results/{id}/
    path('results/', ResultListAPIView.as_view(), name='result_list'),
    path('results/summary/', ResultSummaryAPIView.as_view(), name='result_summary'),
    path('results/<int:pk>/', ResultDetailUpdateAPIView.as_view(), name='result_detail_update'),
]
