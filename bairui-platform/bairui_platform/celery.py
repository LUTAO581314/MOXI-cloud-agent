import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bairui_platform.settings")

app = Celery("bairui_platform")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
