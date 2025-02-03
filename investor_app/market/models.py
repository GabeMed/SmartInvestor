from django.db import models


# Create your models here.
class Assets(models.Model):
    code = models.CharField(max_length=50, unique=True)
    upper_limit = models.DecimalField(max_digits=10, decimal_places=2)
    lower_limit = models.DecimalField(max_digits=10, decimal_places=2)
    periodicy = models.IntegerField(default=5)  # We are using time in minutes

    def __str__(self):
        return self.code


class StockQuote(models.Model):
    asset = models.ForeignKey(Assets, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.asset.code} : {self.price}"