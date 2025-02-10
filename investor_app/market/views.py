from rest_framework import viewsets
from .models import Assets, UserAssets
from .serializers import AssetsSerializer, UserAssetsSerializer


class AssetsViewSet(viewsets.ModelViewSet):
    queryset = Assets.objects.all()
    serializer_class = AssetsSerializer


class UserAssetsViewSet(viewsets.ModelViewSet):
    queryset = UserAssets.objects.all()
    serializer_class = UserAssetsSerializer
