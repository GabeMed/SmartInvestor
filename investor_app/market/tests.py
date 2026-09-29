"""Tests for the market app.

BRAPI is never called: `requests.get` is patched in every test that reaches
it. E-mails go to Django's in-memory outbox (the test runner switches to the
locmem backend automatically).
"""

from datetime import timedelta
from decimal import Decimal
from io import StringIO
from unittest import mock

import requests
from django.contrib.auth import get_user_model
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APITestCase

from market.models import Assets, UserAssets
from market.tasks import fetch_all_stocks, fetch_stock_data, verify_user_stocks

ALERTS_TO = "alerts@example.com"


def brapi_response(payload, status=200):
    """A fake requests.Response for requests.get."""
    response = mock.Mock(status_code=status)
    response.json.return_value = payload
    if status >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(f"{status} error")
    else:
        response.raise_for_status.return_value = None
    return response


def list_payload(*stocks):
    """Shape of GET /api/quote/list."""
    return {"stocks": [{"stock": code, "close": close, "name": code} for code, close in stocks]}


def quote_payload(symbol, price):
    """Shape of GET /api/quote/{ticker}."""
    return {"results": [{"symbol": symbol, "regularMarketPrice": price}]}


def make_asset(code="PETR4", price="38.50"):
    return Assets.objects.create(code=code, price=Decimal(price))


def monitor(asset, lower, upper):
    return UserAssets.objects.create(
        code=asset, lower_limit=Decimal(lower), upper_limit=Decimal(upper)
    )


@override_settings(BRAPI_KEY="test-token", BRAPI_BASE_URL="https://brapi.test/api", BRAPI_TIMEOUT=7, EMAIL_TEST=ALERTS_TO)
class FetchAllStocksTests(TestCase):
    @mock.patch("market.tasks.requests.get")
    def test_creates_and_updates_assets(self, get):
        make_asset("PETR4", "30.00")
        get.return_value = brapi_response(list_payload(("PETR4", 38.5), ("VALE3", 61.234)))

        result = fetch_all_stocks()

        self.assertEqual(result, "2 stocks updated successfully")
        self.assertEqual(Assets.objects.get(code="PETR4").price, Decimal("38.50"))
        self.assertEqual(Assets.objects.get(code="VALE3").price, Decimal("61.23"))

    @mock.patch("market.tasks.requests.get")
    def test_sends_token_in_header_with_timeout(self, get):
        get.return_value = brapi_response(list_payload())

        fetch_all_stocks()

        get.assert_called_once_with(
            "https://brapi.test/api/quote/list",
            headers={"Authorization": "Bearer test-token"},
            timeout=7,
        )

    @override_settings(BRAPI_KEY="")
    @mock.patch("market.tasks.requests.get")
    def test_works_without_token(self, get):
        get.return_value = brapi_response(list_payload(("PETR4", 38.5)))

        fetch_all_stocks()

        self.assertEqual(get.call_args.kwargs["headers"], {})

    @mock.patch("market.tasks.requests.get")
    def test_skips_entries_without_price(self, get):
        get.return_value = brapi_response(
            {"stocks": [{"stock": "PETR4", "close": None}, {"stock": "VALE3", "close": 61.2}, {"close": 1}]}
        )

        result = fetch_all_stocks()

        self.assertEqual(result, "1 stocks updated successfully")
        self.assertEqual(list(Assets.objects.values_list("code", flat=True)), ["VALE3"])

    @mock.patch("market.tasks.requests.get")
    def test_updates_timestamp_on_price_change(self, get):
        asset = make_asset("PETR4", "30.00")
        old = timezone.now() - timedelta(hours=2)
        Assets.objects.filter(pk=asset.pk).update(timestamp=old)
        get.return_value = brapi_response(list_payload(("PETR4", 31)))

        fetch_all_stocks()

        self.assertGreater(Assets.objects.get(pk=asset.pk).timestamp, old)

    @mock.patch("market.tasks.requests.get")
    def test_http_error_changes_nothing(self, get):
        make_asset("PETR4", "30.00")
        get.return_value = brapi_response({"error": True}, status=401)

        result = fetch_all_stocks()

        self.assertEqual(result, "Failed to fetch stocks.")
        self.assertEqual(Assets.objects.get(code="PETR4").price, Decimal("30.00"))

    @mock.patch("market.tasks.requests.get", side_effect=requests.ConnectionError("down"))
    def test_network_error_is_handled(self, get):
        self.assertEqual(fetch_all_stocks(), "Failed to fetch stocks.")

    @mock.patch("market.tasks.requests.get")
    def test_updates_monitored_prices_and_sends_alerts(self, get):
        petr = make_asset("PETR4", "40.00")
        watched = monitor(petr, "35.00", "45.00")
        get.return_value = brapi_response(list_payload(("PETR4", 34.9)))

        fetch_all_stocks()

        watched.refresh_from_db()
        self.assertEqual(watched.price, Decimal("34.90"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("compra", mail.outbox[0].subject)


@override_settings(BRAPI_KEY="", BRAPI_BASE_URL="https://brapi.test/api")
class FetchStockDataTests(TestCase):
    @mock.patch("market.tasks.requests.get")
    def test_uses_symbol_and_regular_market_price(self, get):
        get.return_value = brapi_response(quote_payload("PETR4", 38.5))

        result = fetch_stock_data("PETR4")

        self.assertEqual(result, "Stock PETR4 created successfully.")
        self.assertEqual(Assets.objects.get(code="PETR4").price, Decimal("38.50"))
        self.assertEqual(get.call_args.args[0], "https://brapi.test/api/quote/PETR4")

    @mock.patch("market.tasks.requests.get")
    def test_updates_existing_asset(self, get):
        make_asset("PETR4", "30.00")
        get.return_value = brapi_response(quote_payload("PETR4", 31))

        self.assertEqual(fetch_stock_data("PETR4"), "Stock PETR4 updated successfully.")
        self.assertEqual(Assets.objects.get(code="PETR4").price, Decimal("31.00"))

    @mock.patch("market.tasks.requests.get")
    def test_unknown_ticker(self, get):
        get.return_value = brapi_response({"error": True, "message": "Not found"}, status=404)

        self.assertEqual(fetch_stock_data("XXXX9"), "Failed to fetch stock data.")
        self.assertFalse(Assets.objects.exists())

    @mock.patch("market.tasks.requests.get")
    def test_result_without_price(self, get):
        get.return_value = brapi_response({"results": [{"symbol": "PETR4"}]})

        self.assertEqual(fetch_stock_data("PETR4"), "Failed to fetch stock data.")
        self.assertFalse(Assets.objects.exists())


@override_settings(EMAIL_TEST=ALERTS_TO, DEFAULT_FROM_EMAIL="bot@example.com")
class VerifyUserStocksTests(TestCase):
    def test_buy_alert_below_lower_limit(self):
        monitor(make_asset("PETR4", "30.00"), "35.00", "45.00")

        self.assertEqual(verify_user_stocks(), 1)

        message = mail.outbox[0]
        self.assertEqual(message.to, [ALERTS_TO])
        self.assertEqual(message.from_email, "bot@example.com")
        self.assertIn("compra", message.subject)
        self.assertIn("PETR4", message.subject)
        self.assertIn("R$ 30.00", message.body)
        self.assertIn("R$ 35.00 a R$ 45.00", message.body)

    def test_sell_alert_above_upper_limit(self):
        monitor(make_asset("VALE3", "70.00"), "50.00", "60.00")

        verify_user_stocks()

        self.assertIn("venda", mail.outbox[0].subject)
        self.assertIn("VALE3", mail.outbox[0].subject)

    def test_no_alert_inside_range(self):
        monitor(make_asset("ITUB4", "36.00"), "30.00", "40.00")

        self.assertEqual(verify_user_stocks(), 0)
        self.assertEqual(mail.outbox, [])

    def test_limits_are_inclusive(self):
        monitor(make_asset("PETR4", "35.00"), "35.00", "45.00")
        monitor(make_asset("VALE3", "60.00"), "50.00", "60.00")

        self.assertEqual(verify_user_stocks(), 2)

    def test_one_email_per_asset_out_of_range(self):
        monitor(make_asset("PETR4", "30.00"), "35.00", "45.00")
        monitor(make_asset("VALE3", "70.00"), "50.00", "60.00")
        monitor(make_asset("ITUB4", "36.00"), "30.00", "40.00")

        verify_user_stocks()

        self.assertEqual(sorted(m.subject.split(":")[1].split()[0] for m in mail.outbox), ["PETR4", "VALE3"])

    @override_settings(EMAIL_TEST="")
    def test_skipped_without_recipient(self):
        monitor(make_asset("PETR4", "30.00"), "35.00", "45.00")

        self.assertEqual(verify_user_stocks(), 0)
        self.assertEqual(mail.outbox, [])


class ModelTests(TestCase):
    def test_monitored_price_copies_asset_price(self):
        watched = monitor(make_asset("PETR4", "38.50"), "30.00", "40.00")

        self.assertEqual(watched.price, Decimal("38.50"))

    def test_asset_update_propagates_to_monitored_assets(self):
        asset = make_asset("PETR4", "38.50")
        watched = monitor(asset, "30.00", "40.00")

        asset.price = Decimal("41.00")
        asset.save()

        watched.refresh_from_db()
        self.assertEqual(watched.price, Decimal("41.00"))

    def test_str_is_a_string(self):
        watched = monitor(make_asset("PETR4", "38.50"), "30.00", "40.00")

        self.assertEqual(str(watched), "PETR4 (30.00 - 40.00)")

    def test_lower_limit_must_be_below_upper_limit(self):
        watched = UserAssets(code=make_asset(), lower_limit=Decimal("40"), upper_limit=Decimal("30"))

        with self.assertRaises(ValidationError):
            watched.full_clean()


class AssetsApiTests(APITestCase):
    def test_list_is_paginated_and_sorted(self):
        make_asset("VALE3", "61.20")
        make_asset("PETR4", "38.50")

        response = self.client.get("/assets/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)
        self.assertEqual([a["code"] for a in response.data["results"]], ["PETR4", "VALE3"])

    def test_retrieve_by_code(self):
        make_asset("PETR4", "38.50")

        response = self.client.get("/assets/PETR4/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["price"], "38.50")

    def test_assets_are_read_only(self):
        make_asset("PETR4", "38.50")

        self.assertEqual(self.client.post("/assets/", {"code": "X", "price": "1"}).status_code, 405)
        self.assertEqual(self.client.delete("/assets/PETR4/").status_code, 405)


class FavoriteAssetsApiTests(APITestCase):
    def setUp(self):
        self.asset = make_asset("PETR4", "38.50")

    def test_create_uses_ticker_and_copies_price(self):
        response = self.client.post(
            "/favorite-assets/",
            {"code": "PETR4", "lower_limit": "30.00", "upper_limit": "45.00", "price": "1.00"},
        )

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(response.data["code"], "PETR4")
        self.assertEqual(response.data["price"], "38.50")  # client value ignored

    def test_rejects_unknown_ticker(self):
        response = self.client.post(
            "/favorite-assets/", {"code": "NOPE3", "lower_limit": "1", "upper_limit": "2"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("code", response.data)

    def test_rejects_inverted_limits(self):
        response = self.client.post(
            "/favorite-assets/", {"code": "PETR4", "lower_limit": "45", "upper_limit": "30"}
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("lower_limit", response.data)

    def test_partial_update_validates_against_stored_limits(self):
        watched = monitor(self.asset, "30.00", "45.00")

        bad = self.client.patch(f"/favorite-assets/{watched.pk}/", {"lower_limit": "50"})
        good = self.client.patch(f"/favorite-assets/{watched.pk}/", {"lower_limit": "32.00"})

        self.assertEqual(bad.status_code, 400)
        self.assertEqual(good.status_code, 200)
        self.assertEqual(good.data["lower_limit"], "32.00")

    def test_list_and_delete(self):
        watched = monitor(self.asset, "30.00", "45.00")

        self.assertEqual(self.client.get("/favorite-assets/").data["count"], 1)
        self.assertEqual(self.client.delete(f"/favorite-assets/{watched.pk}/").status_code, 204)
        self.assertFalse(UserAssets.objects.exists())


class AdminTests(TestCase):
    def test_changelists_render(self):
        user = get_user_model().objects.create_superuser("admin", "admin@example.com", "pass")
        self.client.force_login(user)
        monitor(make_asset("PETR4", "38.50"), "30.00", "45.00")

        for url in ("/admin/market/assets/", "/admin/market/userassets/"):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, url)
            self.assertContains(response, "PETR4")


@override_settings(EMAIL_TEST=ALERTS_TO)
class CommandTests(TestCase):
    def test_seed_demo_creates_alerts_once(self):
        out = StringIO()

        call_command("seed_demo", stdout=out)
        call_command("seed_demo", stdout=out)

        self.assertEqual(UserAssets.objects.count(), 3)
        self.assertEqual(sorted(m.subject.split(":")[0] for m in mail.outbox), ["Sugestão de compra", "Sugestão de venda"])
        self.assertIn("nothing to do", out.getvalue())

    @mock.patch("market.tasks.requests.get")
    def test_update_quotes_for_given_tickers(self, get):
        get.side_effect = [
            brapi_response(quote_payload("PETR4", 38.5)),
            brapi_response(quote_payload("VALE3", 61.2)),
        ]
        out = StringIO()

        call_command("update_quotes", "petr4", "VALE3", stdout=out)

        self.assertEqual(set(Assets.objects.values_list("code", flat=True)), {"PETR4", "VALE3"})
        self.assertIn("Stock VALE3 created successfully.", out.getvalue())
