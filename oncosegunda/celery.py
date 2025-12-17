import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oncosegunda.settings')

app = Celery('oncosegunda')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
