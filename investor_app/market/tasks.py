import requests
from django.conf import settings
from celery import shared_task
from market.models import Assets

@shared_task
def fetch_stock_data(stock_symbol):
    url = f"https://brapi.dev/api/quote/{stock_symbol}?token={settings.BRAPI_KEY}"
    response = requests.get(url)
    data = response.json()

    if "results" in data:
        stock_data=data["results"][0]
        stock, created= Assets.objects.update_or_create(
            code=stock_data["stock"],
            defaults={"price": stock_data["close"]}
        )
        return f"Stock {stock.code}{'created' if created else 'updated'} successfully."

    return "Failed to fetch stock data."

@shared_task
def fetch_all_stocks():
    url = f"https://brapi.dev/api/quote/list?token={settings.BRAPI_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        stocks = data.get("stocks", [])

        for stock_data in stocks:
            Assets.objects.update_or_create(
                code=stock_data["stock"],
                defaults={"price": stock_data["close"]}
            )
        
        return f"{len(stocks)} stocks updated successfully"
    
    return "Failed to fetch stocks."