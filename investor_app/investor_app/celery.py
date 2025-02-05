from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Setting the environment variables so celery can access all the settings of the django app
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "investor_app.settings")

celery_app = Celery("investor_app")

celery_app.config_from_object("django.conf:settings", namespace="CELERY")

# Making celery look for the @shared_task annotation 
celery_app.autodiscover_tasks()
