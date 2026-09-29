from decimal import Decimal
from django.core.management.base import BaseCommand
from market.models import Assets, UserAssets
from market.tasks import verify_user_stocks

# Used only if BRAPI hasn't loaded these tickers yet (e.g. no network).
SAMPLE_PRICES = {"PETR4": "38.50", "VALE3": "61.20", "ITUB4": "36.80"}


class Command(BaseCommand):
    help = (
        "Creates three monitored assets whose limits trigger a buy alert, a "
        "sell alert and no alert, then sends the alerts. Does nothing if "
        "monitored assets already exist."
    )

    def handle(self, *args, **options):
        if UserAssets.objects.exists():
            self.stdout.write("Monitored assets already exist; nothing to do.")
            return

        assets = {}
        for code, sample_price in SAMPLE_PRICES.items():
            assets[code], _ = Assets.objects.get_or_create(
                code=code, defaults={"price": Decimal(sample_price)}
            )

        def limits(asset, low, high):
            q = Decimal("0.01")
            return {
                "lower_limit": (asset.price * Decimal(low)).quantize(q),
                "upper_limit": (asset.price * Decimal(high)).quantize(q),
            }

        # Price below the range -> buy ("compra"); above -> sell ("venda").
        UserAssets.objects.create(code=assets["PETR4"], **limits(assets["PETR4"], "1.05", "1.30"))
        UserAssets.objects.create(code=assets["VALE3"], **limits(assets["VALE3"], "0.70", "0.95"))
        UserAssets.objects.create(code=assets["ITUB4"], **limits(assets["ITUB4"], "0.90", "1.10"))

        sent = verify_user_stocks()
        self.stdout.write(f"Created 3 monitored assets and sent {sent} alert(s).")
