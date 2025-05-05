from rest_framework.viewsets import ReadOnlyModelViewSet
from .models import Lawmaker
from .serializers import LawmakerSerializer

class LawmakerViewSet(ReadOnlyModelViewSet):
    queryset = Lawmaker.objects.prefetch_related('bills').all().order_by('seat_number')
    serializer_class = LawmakerSerializer