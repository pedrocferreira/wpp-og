import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')

app = Celery('whatsapp_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

# Configure periodic tasks
app.conf.beat_schedule = {
    'send-appointment-reminders': {
        'task': 'appointments.tasks.send_appointment_reminders',
        'schedule': crontab(minute='*/5'),  # executa a cada 5 minutos
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 