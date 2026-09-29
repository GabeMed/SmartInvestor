from django.core.exceptions import ValidationError
from django.db import models

# Here we will define 2 entities, one for the assets and the other for the user favorite assets

class Assets(models.Model):
    code = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    # Time of the last price update (auto_now_add only kept the creation time).
    timestamp = models.DateTimeField(auto_now=True)

    class Meta:
        # Django would otherwise display "Assetss" in the admin.
        verbose_name = "asset"
        verbose_name_plural = "assets"

    def __str__(self):
        return f"{self.code} : {self.price}"

class UserAssets(models.Model):
    # user = ...ForeignKey(...) if there was an implementation of users it should be referenced here
    code = models.ForeignKey(Assets, on_delete=models.CASCADE)
    upper_limit = models.DecimalField(max_digits=10, decimal_places=2)
    lower_limit = models.DecimalField(max_digits=10, decimal_places=2)
    # Copy of the asset's current price: filled on save and kept in sync by
    # the post_save signal on Assets (see signals.py), so it is not editable.
    price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    periodicy = models.IntegerField(default=5)  # We are using time in minutes

    class Meta:
        verbose_name = "monitored asset"
        verbose_name_plural = "monitored assets"

    def clean(self):
        if (
            self.lower_limit is not None
            and self.upper_limit is not None
            and self.lower_limit >= self.upper_limit
        ):
            raise ValidationError({"lower_limit": "Must be lower than the upper limit."})

    def save(self, *args, **kwargs):
        if self.code_id is not None:
            self.price = self.code.price
        super().save(*args, **kwargs)

    def __str__(self):
        # Must return a str: returning self.code (an Assets instance) broke the admin.
        return f"{self.code.code} ({self.lower_limit} - {self.upper_limit})"
