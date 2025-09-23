#!/usr/bin/env python3

import os
import sys
import django

# Adiciona o diretório do backend ao path
sys.path.append('whatsapp_backend')
os.chdir('whatsapp_backend')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from django.contrib.auth import get_user_model

def create_admin_user():
    User = get_user_model()
    
    email = 'admin@example.com'
    password = 'admin123'
    username = 'admin'
    
    # Remove usuário se existir
    if User.objects.filter(email=email).exists():
        User.objects.filter(email=email).delete()
        print('✅ Usuário admin anterior removido')
    
    if User.objects.filter(username=username).exists():
        User.objects.filter(username=username).delete()
        print('✅ Username admin anterior removido')
    
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
    print(f'🔐 Is Staff: {user.is_staff}')
    print(f'🔑 Is Superuser: {user.is_superuser}')
    
    # Testa autenticação
    from django.contrib.auth import authenticate
    test_user = authenticate(username=email, password=password)
    if test_user:
        print('✅ Autenticação testada com sucesso!')
    else:
        print('❌ Falha no teste de autenticação')
        # Tenta com username
        test_user2 = authenticate(username=username, password=password)
        if test_user2:
            print('✅ Autenticação com username funciona!')
        else:
            print('❌ Autenticação também falhou com username')

if __name__ == '__main__':
    create_admin_user() 