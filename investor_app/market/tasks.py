import logging
from decimal import Decimal, InvalidOperation
import requests
from django.conf import settings
from celery import shared_task
from market.models import Assets, UserAssets
from market.utils import email_alert

logger = logging.getLogger(__name__)


def brapi_get(path):
    """GETs a BRAPI endpoint and returns the decoded JSON, or None on failure.

    The token goes in the Authorization header rather than the query string,
    so it doesn't end up in logs or exception messages.
    """
    headers = {"Authorization": f"Bearer {settings.BRAPI_KEY}"} if settings.BRAPI_KEY else {}
    try:
        response = requests.get(
            f"{settings.BRAPI_BASE_URL}/{path}",
            headers=headers,
            timeout=settings.BRAPI_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("BRAPI request for %s failed: %s", path, type(exc).__name__)
        return None


def to_price(value):
    """BRAPI prices as Decimal, or None for missing/invalid values."""
    if value is None:
        return None
    try:
        return Decimal(str(value)).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


@shared_task
def fetch_stock_data(stock_code):
    data = brapi_get(f"quote/{stock_code}")

    # /quote/{ticker} returns "symbol" and "regularMarketPrice"; the "stock" and
    # "close" keys only exist in /quote/list.
    if data and data.get("results"):
        stock_data = data["results"][0]
        price = to_price(stock_data.get("regularMarketPrice"))
        if stock_data.get("symbol") and price is not None:
            stock, created = Assets.objects.update_or_create(
                code=stock_data["symbol"],
                defaults={"price": price}
            )
            return f"Stock {stock.code} {'created' if created else 'updated'} successfully."

    return "Failed to fetch stock data."

@shared_task
def verify_user_stocks():
    if not settings.EMAIL_TEST:
        logger.warning("EMAIL_TEST is not set; skipping price alerts.")
        return 0

    sent = 0
    for stock in UserAssets.objects.select_related("code"):
        # The limits count as reached when the price touches them.
        if stock.price <= stock.lower_limit:
            email_alert(settings.EMAIL_TEST, "compra", stock)
            sent += 1

        elif stock.price >= stock.upper_limit:
            email_alert(settings.EMAIL_TEST, "venda", stock)
            sent += 1

    return sent

@shared_task
def fetch_all_stocks():
    data = brapi_get("quote/list")
    if data is None:
        return "Failed to fetch stocks."

    updated = 0
    for stock_data in data.get("stocks", []):
        price = to_price(stock_data.get("close"))
        if not stock_data.get("stock") or price is None:
            continue  # BRAPI sometimes lists tickers without a closing price
        Assets.objects.update_or_create(
            code=stock_data["stock"],
            defaults={"price": price}
        )
        updated += 1

    verify_user_stocks()

    return f"{updated} stocks updated successfully"
