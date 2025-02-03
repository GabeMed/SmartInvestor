from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AssetsViewSet, StockQuoteViewSet

router = DefaultRouter()
router.register(r"assets", AssetsViewSet)
router.register(r"stock-quote", StockQuoteViewSet)

urlpatterns = [path("", include(router.urls))]