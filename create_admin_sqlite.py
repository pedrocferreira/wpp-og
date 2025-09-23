#!/usr/bin/env python3

import os
import sys
import django

# Configurar Django para usar SQLite temporariamente
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')

# Adiciona o diretório do backend ao path
backend_path = os.path.join(os.path.dirname(__file__), 'whatsapp_backend')
sys.path.insert(0, backend_path)

# Mudar para o diretório do backend
os.chdir(backend_path)

# Configurar temporariamente para SQLite
os.environ['DB_ENGINE'] = 'sqlite3'
os.environ['DB_NAME'] = 'db.sqlite3'

django.setup()

from django.contrib.auth import get_user_model, authenticate

def create_admin_user():
    User = get_user_model()
    
    # Credenciais conforme especificação do usuário
    email = 'admin@admin.com'
    password = 'admin1234'
    username = 'admin'
    
    print("🔧 Criando usuário admin...")
    
    # Remove usuários existentes
    existing_users = User.objects.filter(email__in=[email, 'admin@example.com'])
    if existing_users.exists():
        for user in existing_users:
            print(f"🗑️ Removendo usuário: {user.email}")
            user.delete()
    
    existing_username = User.objects.filter(username=username)
    if existing_username.exists():
        for user in existing_username:
            print(f"🗑️ Removendo username: {user.username}")
            user.delete()
    
    # Cria novo usuário com credenciais corretas
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name='Admin',
        last_name='Sistema',
        is_staff=True,
        is_superuser=True,
        is_active=True
    )
    
    # Verifica se o campo 'role' existe no modelo
    if hasattr(user, 'role'):
        user.role = 'admin'
        user.save()
    
    print("✅ Usuário admin criado com sucesso!")
    print(f"📧 Email: {email}")
    print(f"🔑 Senha: {password}")
    print(f"🆔 ID: {user.id}")
    print(f"👤 Username: {username}")
    print(f"🔐 Is Staff: {user.is_staff}")
    print(f"🔑 Is Superuser: {user.is_superuser}")
    print(f"✅ Is Active: {user.is_active}")
    
    # Teste de autenticação
    print("\n🧪 Testando autenticação...")
    
    # Teste 1: Autenticação por email
    test_user1 = authenticate(username=email, password=password)
    if test_user1:
        print("✅ Autenticação por email: SUCESSO")
    else:
        print("❌ Autenticação por email: FALHOU")
    
    # Teste 2: Autenticação por username
    test_user2 = authenticate(username=username, password=password)
    if test_user2:
        print("✅ Autenticação por username: SUCESSO")
    else:
        print("❌ Autenticação por username: FALHOU")
    
    # Listar todos os usuários
    print("\n👥 Usuários no sistema:")
    for u in User.objects.all():
        print(f"- Email: {u.email}, Username: {u.username}, Ativo: {u.is_active}")
    
    print("\n🎯 CREDENCIAIS PARA TESTE:")
    print(f"Email: {email}")
    print(f"Senha: {password}")

if __name__ == '__main__':
    create_admin_user()