from django.urls import path
from .views import JobListCreateAPIView, JobDetailAPIView, JobResumeAPIView

app_name = 'processing'

urlpatterns = [
    path('jobs/', JobListCreateAPIView.as_view(), name='job_list_create'),
    path('jobs/<int:pk>/', JobDetailAPIView.as_view(), name='job_detail'),
    path('jobs/<int:pk>/resume/', JobResumeAPIView.as_view(), name='job_resume'),
]
