from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.beat import crontab

# Setting the environment variables so celery can access all the settings of the django app
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "investor_app.settings")

app = Celery("investor_app", include=["market.tasks"])

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

# Config of the periodic tasks
app.conf.beat_schedule = {
    "fetch_all_stocks_every_hour": {
        "task": "market.tasks.fetch_all_stocks",
        "schedule": crontab(minute=0, hour="*"), # Here we define the periodicy of the updates of each asset information
    }
}
