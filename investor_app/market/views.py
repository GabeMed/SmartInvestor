from rest_framework import viewsets
from .models import Assets, StockQuote
from .serializers import AssetsSerializer, StockQuoteSerializer



# Create your views here.
class AssetsViewSet(viewsets.ModelViewSet):
    queryset = Assets.objects.all()
    serializer_class = AssetsSerializer


class StockQuoteViewSet(viewsets.ModelViewSet):
    queryset = StockQuote.objects.all()
    serializer_class = StockQuoteSerializer
