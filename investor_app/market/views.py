from rest_framework import viewsets
from .models import Assets, UserAssets
from .serializers import AssetsSerializer, UserAssetsSerializer


class AssetsViewSet(viewsets.ReadOnlyModelViewSet):
    """Quotes fetched from BRAPI. Read-only: prices come from the Celery tasks."""

    queryset = Assets.objects.order_by("code")
    serializer_class = AssetsSerializer
    lookup_field = "code"


class UserAssetsViewSet(viewsets.ModelViewSet):
    """Monitored assets and their price limits."""

    queryset = UserAssets.objects.select_related("code").order_by("id")
    serializer_class = UserAssetsSerializer
