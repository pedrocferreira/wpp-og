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
# Configuração de filas otimizadas
app.conf.task_routes = {
    # Filas de alta prioridade
    'whatsapp.tasks.send_whatsapp_message_async': {'queue': 'high_priority'},
    'whatsapp.tasks.send_delayed_message_async': {'queue': 'normal'},
    'whatsapp.tasks.process_webhook_async': {'queue': 'high_priority'},
    
    # Filas de monitoramento
    'whatsapp.tasks.health_check_evolution_api': {'queue': 'monitoring'},
    'whatsapp.tasks.monitor_message_queue': {'queue': 'monitoring'},
    'whatsapp.tasks.cleanup_old_messages': {'queue': 'maintenance'},
    
    # Filas de agendamentos
    'appointments.tasks.send_appointment_reminders': {'queue': 'normal'},
    'appointments.tasks.create_missing_reminders': {'queue': 'maintenance'},
    'appointments.tasks.check_expired_appointments': {'queue': 'maintenance'},
    'appointments.tasks.send_followup_messages': {'queue': 'normal'},
}

# Configuração de workers por fila
app.conf.worker_routes = {
    'high_priority': {'concurrency': 4},
    'normal': {'concurrency': 2},
    'monitoring': {'concurrency': 1},
    'maintenance': {'concurrency': 1},
}

# Configuração de rate limits
app.conf.task_annotations = {
    'whatsapp.tasks.send_whatsapp_message_async': {'rate_limit': '10/m'},  # 10 por minuto
    'whatsapp.tasks.health_check_evolution_api': {'rate_limit': '1/m'},   # 1 por minuto
}

app.conf.beat_schedule = {
    'send-appointment-reminders': {
        'task': 'appointments.tasks.send_appointment_reminders',
        'schedule': crontab(minute='*/2'),  # executa a cada 2 minutos para garantir pontualidade
    },
    'send-custom-reminders': {
        'task': 'appointments.tasks.send_custom_reminders',
        'schedule': crontab(minute='*/2'),  # executa a cada 2 minutos para garantir pontualidade
    },
    'create-missing-reminders': {
        'task': 'appointments.tasks.create_missing_reminders',
        'schedule': crontab(minute=0, hour='*/6'),  # executa a cada 6 horas
    },
    'check-expired-appointments': {
        'task': 'appointments.tasks.check_expired_appointments',
        'schedule': crontab(minute=0, hour=1),  # executa diariamente à 1h
    },
    'send-followup-messages': {
        'task': 'appointments.tasks.send_followup_messages',
        'schedule': crontab(minute=0, hour=10),  # executa diariamente às 10h
    },
    # === NOVAS TAREFAS DE MONITORAMENTO ===
    'monitor-message-queue': {
        'task': 'whatsapp.tasks.monitor_message_queue',
        'schedule': crontab(minute='*/5'),  # executa a cada 5 minutos
    },
    'health-check-evolution': {
        'task': 'whatsapp.tasks.health_check_evolution_api',
        'schedule': crontab(minute='*/10'),  # executa a cada 10 minutos
    },
    'cleanup-old-messages': {
        'task': 'whatsapp.tasks.cleanup_old_messages',
        'schedule': crontab(minute=0, hour=2),  # executa diariamente às 2h
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 