from django.contrib import admin
from .models import Assets, UserAssets

@admin.register(Assets)
class AssetsAdmin(admin.ModelAdmin):
    list_display = ('code', 'price', 'timestamp')
    search_fields = ('code',)
    ordering = ('-timestamp',)

@admin.register(UserAssets)
class UserAssetsAdmin(admin.ModelAdmin):
    list_display = ('code', 'upper_limit', 'lower_limit', 'periodicy')
    search_fields = ('code__code',)
    ordering = ('code',)