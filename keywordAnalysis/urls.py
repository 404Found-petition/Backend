# 위 View를 URL에 연결
from django.urls import path
from .views import PetitionStatisticsAPIView

urlpatterns = [
    path("statistics/", PetitionStatisticsAPIView.as_view()),  # → /api/statistics/
]
