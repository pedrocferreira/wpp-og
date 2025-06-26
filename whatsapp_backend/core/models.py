from django.db import models
from django.conf import settings
import json

class GoogleCalendarCredentials(models.Model):
    """Armazena as credenciais OAuth2 do Google Calendar"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='google_credentials')
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_uri = models.URLField(default='https://oauth2.googleapis.com/token')
    client_id = models.CharField(max_length=255)
    client_secret = models.CharField(max_length=255)
    scopes = models.JSONField(default=list)
    expiry = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Credencial Google Calendar'
        verbose_name_plural = 'Credenciais Google Calendar'
    
    def __str__(self):
        return f"Credenciais Google - {self.user.username}"
    
    def to_dict(self):
        """Converte as credenciais para o formato esperado pela biblioteca Google"""
        return {
            'token': self.access_token,
            'refresh_token': self.refresh_token,
            'token_uri': self.token_uri,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scopes': self.scopes,
            'expiry': self.expiry.isoformat() if self.expiry else None
        }

class GoogleCalendarSettings(models.Model):
    """Configurações do Google Calendar para a clínica"""
    calendar_id = models.CharField(max_length=255, default='primary')
    appointment_duration = models.IntegerField(default=60)  # em minutos
    buffer_time = models.IntegerField(default=15)  # tempo entre consultas
    work_days = models.JSONField(default=list)  # [0,1,2,3,4] para seg-sex
    work_hours_start = models.TimeField(default='08:00')
    work_hours_end = models.TimeField(default='18:00')
    lunch_start = models.TimeField(default='12:00')
    lunch_end = models.TimeField(default='14:00')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Configuração Google Calendar'
        verbose_name_plural = 'Configurações Google Calendar'
    
    def __str__(self):
        return f"Configurações Calendar - {self.calendar_id}"

class AISettings(models.Model):
    """Configurações da assistente de IA"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_settings')
    assistant_name = models.CharField(max_length=100, default='Elô')
    personality = models.TextField(default='Sou uma assistente calorosa, empática e profissional.')
    clinic_info = models.TextField(default='Clínica especializada em saúde mental e bem-estar.')
    doctor_name = models.CharField(max_length=100, default='Dra. Elisa Munaretti')
    doctor_specialties = models.JSONField(default=list)
    working_hours = models.CharField(max_length=200, default='Segunda a sexta: 8h às 18h')
    appointment_duration = models.IntegerField(default=60)
    response_style = models.CharField(
        max_length=50, 
        choices=[
            ('formal', 'Formal e profissional'),
            ('friendly', 'Amigável e caloroso'),
            ('casual', 'Descontraído e informal'),
            ('empathetic', 'Empático e acolhedor'),
        ],
        default='empathetic'
    )
    use_emojis = models.BooleanField(default=True)
    auto_scheduling = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user']
        verbose_name = 'Configuração da IA'
        verbose_name_plural = 'Configurações da IA'

    def __str__(self):
        return f'Configurações IA - {self.assistant_name} ({self.user.username})'
