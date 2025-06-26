from django.db import models
from django.conf import settings
from django.utils import timezone
from authentication.models import User

class Client(models.Model):
    name = models.CharField(max_length=255)
    whatsapp = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Agendado'),
        ('confirmed', 'Confirmado'),
        ('cancelled', 'Cancelado'),
        ('completed', 'Concluído'),
        ('no_show', 'Não Compareceu'),
    ]

    SOURCE_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('site', 'Site'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    duration = models.IntegerField(default=60)  # duração em minutos
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='whatsapp')
    description = models.TextField(blank=True)
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)  # ID do evento no Google Calendar
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.client.name} - {self.date_time.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        ordering = ['date_time']

class AppointmentReminder(models.Model):
    REMINDER_TYPES = [
        ('2_days', '2 dias antes'),
        ('1_day', '1 dia antes'),
        ('same_day', 'No dia'),
    ]

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    scheduled_for = models.DateTimeField()
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Lembrete {self.get_reminder_type_display()} - {self.appointment}"

    def mark_as_sent(self, response=None):
        self.sent = True
        self.sent_at = timezone.now()
        if response:
            self.response = response
        self.save()

    class Meta:
        ordering = ['scheduled_for']
        unique_together = ['appointment', 'reminder_type']

class ConversationState(models.Model):
    client = models.OneToOneField(Client, on_delete=models.CASCADE)
    step = models.CharField(max_length=50, default='start')  # Ex: 'awaiting_date', 'awaiting_time', 'awaiting_type', 'completed'
    temp_date = models.DateField(null=True, blank=True)
    temp_time = models.TimeField(null=True, blank=True)
    temp_type = models.CharField(max_length=100, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Estado de {self.client.name}: {self.step}"
