from django.db import models
from django.conf import settings
from authentication.models import Client, User
from django.utils import timezone

class WhatsAppMessage(models.Model):
    MESSAGE_TYPES = [
        ('RECEIVED', 'Recebida'),
        ('SENT', 'Enviada'),
        ('NOTIFICATION', 'Notificação'),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='RECEIVED')
    content = models.TextField()
    media_url = models.URLField(blank=True, null=True)
    media_type = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default='sent')
    processed_by_ai = models.BooleanField(default=False)
    message_id = models.CharField(max_length=100, blank=True, null=True)
    direction = models.CharField(max_length=20, choices=[('SENT', 'Enviada'), ('RECEIVED', 'Recebida')], default='RECEIVED')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Mensagem {self.get_message_type_display()} de {self.client.name}"

class AIResponse(models.Model):
    message = models.ForeignKey(WhatsAppMessage, on_delete=models.CASCADE)
    response_text = models.TextField()
    confidence_score = models.FloatField()
    intent_detected = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Resposta IA para {self.message}"

class WebhookLog(models.Model):
    payload = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"Webhook recebido em {self.timestamp}"

class EvolutionConfig(models.Model):
    instance_id = models.CharField(max_length=255)
    api_key = models.CharField(max_length=255)
    webhook_url = models.URLField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Evolution API Configuration"
        verbose_name_plural = "Evolution API Configurations"

    def __str__(self):
        return f"Evolution Config - {self.instance_id}"

class Conversation(models.Model):
    whatsapp_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('active', 'Ativa'),
            ('waiting', 'Aguardando'),
            ('completed', 'Concluída')
        ],
        default='active'
    )
    
    class Meta:
        ordering = ['-updated_at']

class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_from_bot = models.BooleanField(default=False)
    intent = models.CharField(max_length=50, null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']
