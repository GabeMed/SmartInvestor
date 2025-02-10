from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetsViewSet, UserAssetsViewSet

router = DefaultRouter()
router.register(r"assets", AssetsViewSet)
router.register(r"favorite-assets", UserAssetsViewSet)

urlpatterns = [path("", include(router.urls))]