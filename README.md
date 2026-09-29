# SmartInvestor

[![CI](https://github.com/GabeMed/SmartInvestor/actions/workflows/ci.yml/badge.svg)](https://github.com/GabeMed/SmartInvestor/actions/workflows/ci.yml)

A Django app that monitors Brazilian stock prices and e-mails buy or sell
suggestions. You choose the assets to watch and a price range for each; every
hour a Celery task pulls quotes for about 2000 tickers from the
[BRAPI](https://brapi.dev) API. When a watched price reaches the bottom of its
range you get a buy ("compra") e-mail, and at the top a sell ("venda") e-mail.

Stack: Django 5.2, Django REST Framework, Celery + Redis, django-celery-beat,
PostgreSQL (or SQLite), django-admin-interface.

| Monitored assets in the Django admin | Alert e-mail (caught locally by Mailpit) |
| --- | --- |
| ![Django admin listing monitored assets with price and limits](docs/screenshots/admin-monitored-assets.png) | ![Buy alert e-mail for PETR4](docs/screenshots/mailpit-alert.png) |

## Quick start

Requires Docker. No BRAPI token or SMTP account is needed.

```bash
git clone https://github.com/GabeMed/SmartInvestor.git
cd SmartInvestor
docker compose up --build
```

| URL | What |
| --- | --- |
| http://localhost:8000/admin | Django admin. Log in with **admin / admin** (a local-only user created on startup). |
| http://localhost:8000/ | REST API (browsable). |
| http://localhost:8025 | Mailpit inbox with the alert e-mails. |

On startup the web container runs the migrations, loads the current quotes
from BRAPI once, and creates three demo monitored assets (`seed_demo`). Their
ranges are set around the current prices so that one produces a buy alert, one
a sell alert and one no alert, which means two e-mails are waiting in Mailpit.
After that, Celery beat refreshes quotes and checks alerts every hour.

Optional: `BRAPI_KEY=... docker compose up` uses your token. Without one, the
quote list and a few tickers (PETR4, VALE3, MGLU3, ITUB4) still work. If BRAPI
can't be reached, the app starts anyway and `seed_demo` falls back to sample
prices.

## Architecture

```mermaid
flowchart LR
    User(("User")) --> Web["Django<br/>REST API + admin"]
    Web --> DB[("PostgreSQL<br/>(SQLite locally)")]

    Beat["Celery beat<br/>hourly, DatabaseScheduler"] -- "fetch_all_stocks" --> Redis[("Redis<br/>broker")]
    Redis --> Worker["Celery worker"]
    Worker -- "GET /api/quote/list" --> BRAPI["brapi.dev"]
    Worker -- "upsert Assets" --> DB
    Worker -- "verify_user_stocks" --> SMTP["SMTP<br/>(Mailpit locally)"]
```

Code layout (`investor_app/`):

| Path | Role |
| --- | --- |
| `market/models.py` | `Assets` holds the latest quote per ticker. `UserAssets` is a monitored asset with `lower_limit`/`upper_limit` and a copy of the current price. |
| `market/tasks.py` | Celery tasks: `fetch_all_stocks` (every ticker, then checks the alerts), `fetch_stock_data` (one ticker) and `verify_user_stocks`. |
| `market/signals.py` | A `post_save` hook on `Assets` copies the new price to every `UserAssets` watching it. |
| `market/utils.py` | Builds and sends the alert e-mail. |
| `market/views.py`, `serializers.py`, `urls.py` | DRF viewsets. |
| `market/admin.py` | Admin for assets and monitored assets. |
| `market/management/commands/` | `update_quotes` and `seed_demo`. |
| `investor_app/celery.py` | Celery app and the hourly beat schedule. |
| `investor_app/settings.py` | All configuration comes from environment variables (see below). |

**Update cycle.** `fetch_all_stocks` calls `GET /api/quote/list` and upserts
one `Assets` row per ticker. It skips entries with no closing price and logs
BRAPI errors instead of crashing. Each save fires the signal that updates the
monitored copies. `verify_user_stocks` then sends one e-mail per monitored
asset whose price is at or below `lower_limit` (buy) or at or above
`upper_limit` (sell). The BRAPI token goes in the `Authorization` header, so it
never appears in URLs or logs.

## API

| Method | Route | Description |
| --- | --- | --- |
| GET | `/assets/?page=N` | Quotes, 50 per page, sorted by ticker. Read-only, because prices come from BRAPI. |
| GET | `/assets/{code}/` | One quote, e.g. `/assets/PETR4/`. |
| GET, POST | `/favorite-assets/` | List monitored assets, or create one: `{"code": "PETR4", "lower_limit": "30.00", "upper_limit": "45.00"}`. The price is filled in from the asset. |
| GET, PUT, PATCH, DELETE | `/favorite-assets/{id}/` | Read, update or delete a monitored asset. `lower_limit` must be below `upper_limit`. |

## Running without Docker

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cd investor_app
python manage.py migrate            # SQLite: investor_app/local.sqlite3
python manage.py createsuperuser
python manage.py update_quotes      # fetch quotes now (or: update_quotes PETR4 VALE3)
python manage.py seed_demo          # optional demo monitored assets + alerts
python manage.py runserver
```

E-mails are printed to the console unless SMTP is configured. For the hourly
schedule, run Redis and then `celery -A investor_app worker` and
`celery -A investor_app beat` from `investor_app/`.

## Tests

```bash
cd investor_app
python manage.py test
DATABASE_URL=postgres://user:pass@localhost:5432/db python manage.py test   # on PostgreSQL
ruff check ..
```

The 33 tests need no network and no credentials. BRAPI is mocked at
`requests.get` and e-mails go to Django's in-memory outbox. They cover:

- **BRAPI tasks:** creating and updating quotes from both endpoints, the `Authorization` header and timeout, running without a token, entries without a price, HTTP and network errors, timestamp updates.
- **Alerts:** buy and sell e-mails with the ticker, price and range; no e-mail inside the range; inclusive limits; one e-mail per asset; skipping when no recipient is configured.
- **Models and API:** price propagation through the signal, limit validation (including PATCH against stored values), unknown tickers, read-only assets, pagination.
- **Admin and commands:** changelists render; `seed_demo` is idempotent and produces the two expected alerts; `update_quotes` with tickers.

[CI](.github/workflows/ci.yml) runs ruff, `manage.py check`, a missing-migrations
check and the tests on SQLite and PostgreSQL. It then runs `docker compose up
--wait` and checks that the demo data is served and both alerts reached
Mailpit.

## Configuration

Everything is optional. Settings are read from the environment or from
`investor_app/.env` (see [`.env.example`](investor_app/.env.example)).

| Variable | Default | Purpose |
| --- | --- | --- |
| `BRAPI_KEY` | empty | BRAPI token. |
| `EMAIL_TEST` | empty | Recipient of the alerts. Alerts are skipped if unset. |
| `EMAIL_BACKEND` | console backend | Use `django.core.mail.backends.smtp.EmailBackend` to send. |
| `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Gmail SMTP, no credentials | SMTP settings. |
| `DATABASE_URL` | `sqlite:///investor_app/local.sqlite3` | e.g. `postgres://user:pass@host:5432/db`. |
| `CELERY_BROKER_URL` | `redis://127.0.0.1:6379/0` | Celery broker. |
| `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS` | development values | Set these for any real deployment. |

## Limitations

- There are no user accounts yet (see the comment in `UserAssets`): monitored assets are shared, alerts go to the single `EMAIL_TEST` address, and the API has no authentication. It is meant for local use.
- While a price stays outside its range, the alert is sent again every hour; there is no de-duplication.
- `UserAssets.periodicy` is stored but not used. Every asset is checked on the same hourly schedule.
- The Docker setup uses Django's development server.

---

## Em português

SmartInvestor monitora ativos da B3: você define uma faixa de preço para cada
ativo favorito e, a cada hora, uma tarefa Celery atualiza as cotações pela API
BRAPI e envia um e-mail de sugestão de compra (preço no limite inferior ou
abaixo) ou de venda (no limite superior ou acima).

```bash
docker compose up --build
# admin: http://localhost:8000/admin (admin / admin) · API: http://localhost:8000/ · e-mails: http://localhost:8025
```

Não é preciso token da BRAPI nem conta de e-mail. Sem SMTP configurado, os
e-mails aparecem no console (ou no Mailpit, com Docker). Para rodar sem
Docker, testar e configurar as variáveis de ambiente, veja as seções acima.
