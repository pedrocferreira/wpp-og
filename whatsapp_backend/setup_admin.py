#!/usr/bin/env python
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def setup_admin():
    email = 'admin@admin.com'
    password = 'admin123'
    username = 'admin'
    
    # Remove usuário se existir
    if User.objects.filter(email=email).exists():
        User.objects.filter(email=email).delete()
        print('✅ Usuário admin anterior removido')
    
    # Cria novo usuário
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name='Admin',
        last_name='Sistema',
        role='admin',
        is_staff=True,
        is_superuser=True
    )
    
    print('🎉 Usuário admin criado com sucesso!')
    print(f'📧 Email: {email}')
    print(f'🔑 Senha: {password}')
    print(f'🆔 ID: {user.id}')
    print(f'👤 Username: {username}')

if __name__ == '__main__':
    setup_admin() 