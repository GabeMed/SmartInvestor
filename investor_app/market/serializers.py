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
        # price is copied from the asset (UserAssets.price is not editable)

    def validate(self, attrs):
        # On PATCH only some fields are sent; compare against the stored ones.
        lower = attrs.get("lower_limit", getattr(self.instance, "lower_limit", None))
        upper = attrs.get("upper_limit", getattr(self.instance, "upper_limit", None))
        if lower is not None and upper is not None and lower >= upper:
            raise serializers.ValidationError(
                {"lower_limit": "Must be lower than the upper limit."}
            )
        return attrs
