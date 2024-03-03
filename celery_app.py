import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'joomys.settings')

app = Celery('joomys')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.conf.broker_url = settings.CELERY_BROKER_URL
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'scrap_now_task': {
        'task': 'scrap_vacancy.tasks.scrap_now',  # Путь к вашей функции scrap_now
        'schedule': crontab(hour=13, minute=56),  # Запускать ежедневно в 19:00
    },
}
