from rest_framework.views import APIView
from rest_framework.response import Response
from .models import FieldSummary

class PetitionStatisticsAPIView(APIView):
    def get(self, request):
        data = list(FieldSummary.objects.values("분야", "청원수", "색상"))
        return Response(data)
