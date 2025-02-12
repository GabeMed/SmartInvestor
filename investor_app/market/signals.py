from django.db.models.signals import post_save 
from django.dispatch import receiver
from market.models import Assets, UserAssets

@receiver(post_save, sender = Assets)
def update_user_assets_price(sender, instance, **kwargs):
    "This signal works as a trigger, and everytime the Assets are updated, the UserAssets are going to be updated as well"
    UserAssets.objects.filter(code=instance).update(price=instance.price)