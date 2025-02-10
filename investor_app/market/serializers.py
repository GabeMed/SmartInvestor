from rest_framework import serializers
from .models import Assets, UserAssets


class AssetsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Assets
        fields = "__all__"


class UserAssetsSerializer(serializers.ModelSerializer):
    code = serializers.SlugRelatedField(
        queryset=Assets.objects.all(), slug_field="code"
    )

    class Meta:
        model = UserAssets
        fields = "__all__"
