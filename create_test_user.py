#!/usr/bin/env python
import os
import sys
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
sys.path.append('/root/wpp-og/whatsapp_backend')
django.setup()

from authentication.models import User

# Criar usuário de teste
try:
    # Remover usuário se existir
    User.objects.filter(email='teste@teste.com').delete()
    
    # Criar novo usuário
    user = User.objects.create_user(
        username='teste',
        email='teste@teste.com',
        password='123456',
        first_name='Usuário',
        last_name='Teste',
        role='admin',
        is_staff=True,
        is_superuser=True
    )
    
    print(f"Usuário criado com sucesso!")
    print(f"Email: {user.email}")
    print(f"Senha: 123456")
    print(f"Username: {user.username}")
    
except Exception as e:
    print(f"Erro ao criar usuário: {e}") 