from django.db import models

# Here we will define 2 entities, one for the assets and the other for the user favorite assets

class Assets(models.Model):
    code = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} : {self.price}"

class UserAssets(models.Model):
    # user = ...ForeignKey(...) if there was an implementation of users it should be referenced here
    code = models.ForeignKey(Assets, on_delete=models.CASCADE)
    upper_limit = models.DecimalField(max_digits=10, decimal_places=2)
    lower_limit = models.DecimalField(max_digits=10, decimal_places=2)
    periodicy = models.IntegerField(default=5)  # We are using time in minutes

    def __str__(self):
        return self.code