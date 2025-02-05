from celery import shared_task
import requests
from django.conf import settings

@shared_task
def fetch_stock_data(stock_symbol):
    url = f"https://brapi.dev/api/quote/{stock_symbol}?token={settings.BRAPI_KEY}"
    response = requests.get(url)
    data = response.json()

    if "results" in data:
        return data["results"][0]["regularMarketPrice"]

    return None
