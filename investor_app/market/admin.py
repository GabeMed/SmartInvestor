from django.contrib import admin
from .models import Assets, UserAssets

@admin.register(Assets)
class AssetsAdmin(admin.ModelAdmin):
    list_display = ('code', 'price', 'timestamp')
    search_fields = ('code',)
    ordering = ('-timestamp',)

@admin.register(UserAssets)
class UserAssetsAdmin(admin.ModelAdmin):
    list_display = ('code', 'price', 'lower_limit', 'upper_limit', 'periodicy')
    readonly_fields = ('price',)
    autocomplete_fields = ('code',)  # ~2000 assets: a plain <select> is unusable
    search_fields = ('code__code',)
    ordering = ('code',)