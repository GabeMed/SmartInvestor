from rest_framework import serializers
from .models import Assets, StockQuote


class AssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = "__all__"


class StockQuoteSerializer(serializers.ModelSerializer):
    asset = serializers.SlugRelatedField(
        queryset=Assets.objects.all(), slug_field="code"
    )

    class Meta:
        model = StockQuote
        fields = "__all__"
