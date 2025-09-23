from django.db import models
from django.utils import timezone
from datetime import timedelta
from authentication.models import Client
import pytz

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('scheduled', 'Agendada'),
        ('confirmed', 'Confirmada'),
        ('completed', 'Concluída'),
        ('cancelled', 'Cancelada'),
        ('no_show', 'Não compareceu'),
    ]
    
    SOURCE_CHOICES = [
        ('whatsapp', 'WhatsApp'),
        ('site', 'Site'),
        ('phone', 'Telefone'),
        ('admin', 'Administrativo'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    date_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='whatsapp')
    description = models.TextField(blank=True, null=True)
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date_time']

    def __str__(self):
        return f"{self.client.name} - {self.date_time.strftime('%d/%m/%Y %H:%M')}"

class AppointmentReminder(models.Model):
    REMINDER_TYPES = [
        ('1_day', '1 dia antes'),
        ('2_hours', '2 horas antes'),
        ('same_day', 'No dia'),
        ('custom', 'Personalizado'),
    ]

    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    scheduled_for = models.DateTimeField()
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    response = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Campos para lembretes personalizados
    custom_message = models.TextField(blank=True, null=True)
    custom_timing = models.CharField(max_length=100, blank=True, null=True)  # "2 horas antes", "1 semana antes", etc.

    def __str__(self):
        return f"Lembrete {self.get_reminder_type_display()} - {self.appointment}"

    def mark_as_sent(self, response=None):
        self.sent = True
        self.sent_at = timezone.now()
        if response:
            self.response = response
        self.save()

    def get_reminder_message(self):
        """Gera mensagem personalizada para cada tipo de lembrete"""
        client_name = self.appointment.client.name
        date_str = self.appointment.date_time.strftime('%d/%m/%Y')
        time_str = self.appointment.date_time.strftime('%H:%M')
        
        # Determina o dia da semana em português
        weekdays = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
        weekday = weekdays[self.appointment.date_time.weekday()]
        
        if self.reminder_type == '1_day':
            return (
                f"Oi, {client_name}! 😊\n\n"
                f"Só lembrando que você tem consulta agendada amanhã, {weekday} ({date_str}) às {time_str}.\n\n"
                f"Se não puder vir, me avise com antecedência, tá? Assim posso reagendar pra outro horário que funcione melhor pra você!\n\n"
                f"Até amanhã! 💙"
            )
        elif self.reminder_type == '2_hours':
            return (
                f"Oi, {client_name}! ⏰\n\n"
                f"Sua consulta é daqui a 2 horas (às {time_str}).\n\n"
                f"Já está se preparando pra vir? Se houver algum imprevisto, me avise o quanto antes!\n\n"
                f"Te esperamos aqui! 😊"
            )
        elif self.reminder_type == 'custom' and self.custom_message:
            return self.custom_message
        else:
            return (
                f"Oi, {client_name}!\n\n"
                f"Lembrando da sua consulta em {date_str} às {time_str}.\n\n"
                f"Qualquer dúvida, me chame!"
            )

    class Meta:
        ordering = ['scheduled_for']
        unique_together = ['appointment', 'reminder_type']

class CustomReminderRequest(models.Model):
    """Modelo para registrar pedidos de lembretes personalizados dos clientes"""
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, null=True, blank=True)
    request_text = models.TextField()  # Texto original do pedido: "me avisa 2 horas antes"
    reminder_timing = models.CharField(max_length=100)  # "2 horas antes", "1 semana antes", etc.
    scheduled_for = models.DateTimeField()
    message = models.TextField()  # Mensagem personalizada
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['scheduled_for']
    
    def __str__(self):
        return f"Lembrete personalizado para {self.client.name} - {self.reminder_timing}"
    
    def mark_as_sent(self):
        self.sent = True
        self.sent_at = timezone.now()
        self.save()
