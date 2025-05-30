"""
URL configuration for petition project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from lawmembers.views import LawmakerViewSet
from ai.views import PublicPredictionListView
from django.conf import settings
from django.conf.urls.static import static

router = DefaultRouter()
router.register(r'lawmembers', LawmakerViewSet)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('petition.gov.urls')),  # 모든 API는 gov/urls.py에서 정의
    path('api/', include(router.urls)),
    path("api/", include("keywordAnalysis.urls")),
    path('api/lawmembers/', include('lawmembers.urls')),
    path("api/public-predictions/", PublicPredictionListView.as_view()),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
