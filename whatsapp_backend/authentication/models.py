from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Modelo de usuário personalizado para o sistema
    """
    ROLE_CHOICES = [
        ('admin', 'Administrador'),
        ('attendant', 'Atendente'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='attendant')
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_online = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

class Client(models.Model):
    name = models.CharField(max_length=255)
    whatsapp = models.CharField(max_length=20, unique=True)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    last_interaction = models.DateTimeField(auto_now=True)
    notes = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.whatsapp})"

    class Meta:
        ordering = ['-created_at']
