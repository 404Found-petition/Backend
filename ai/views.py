# ai/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import CsvPrediction
from .serializers import CsvPredictionSerializer

class PublicPredictionListView(APIView):
    def get(self, request):
        queryset = CsvPrediction.objects.all()
        serializer = CsvPredictionSerializer(queryset, many=True)
        return Response({
            "success": True,
            "data": serializer.data
        })
