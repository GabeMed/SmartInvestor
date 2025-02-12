import requests
from django.conf import settings
from celery import shared_task
from market.models import Assets, UserAssets
from market.utils import email_alert

@shared_task
def fetch_stock_data(stock_code):
    url = f"https://brapi.dev/api/quote/{stock_code}?token={settings.BRAPI_KEY}"
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
def verify_user_stocks():
    user_stocks = UserAssets.objects.all()
    
    for stock in user_stocks:
        
        if stock.price < stock.lower_limit:
            email_alert(settings.EMAIL_TEST,"compra")
        
        elif stock.price > stock.upper_limit:
            email_alert(settings.EMAIL_TEST,"venda")
    
    return None

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
        
        verify_user_stocks()

        return f"{len(stocks)} stocks updated successfully"
    
    return "Failed to fetch stocks."