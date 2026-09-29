from django.core.management.base import BaseCommand
from market.tasks import fetch_all_stocks, fetch_stock_data


class Command(BaseCommand):
    help = (
        "Fetches quotes from BRAPI now, without waiting for Celery beat. "
        "With no arguments, updates every listed stock and checks the alerts."
    )

    def add_arguments(self, parser):
        parser.add_argument("tickers", nargs="*", help="Only these tickers, e.g. PETR4 VALE3")

    def handle(self, *args, tickers, **options):
        if not tickers:
            self.stdout.write(fetch_all_stocks())
        for ticker in tickers:
            self.stdout.write(fetch_stock_data(ticker.upper()))
