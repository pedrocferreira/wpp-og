#!/usr/bin/env python3

import os
import sys
import django

# Configurar o caminho do Django
sys.path.append('/root/wpp-og/whatsapp_backend')
os.chdir('/root/wpp-og/whatsapp_backend')

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')

# Forçar uso do SQLite
os.environ['DB_ENGINE'] = 'sqlite3'
os.environ['DB_NAME'] = 'db.sqlite3'

django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

def create_admin_user():
    User = get_user_model()
    
    # Credenciais do admin
    email = 'admin@admin.com'
    password = 'admin1234'
    username = 'admin'
    
    print("🔧 Criando usuário admin...")
    print(f"📊 Usando banco: {connection.settings_dict['NAME']}")
    
    try:
        # Limpar usuários admin existentes
        User.objects.filter(email__in=[email, 'admin@example.com']).delete()
        User.objects.filter(username=username).delete()
        print("🗑️ Usuários existentes removidos")
        
        # Criar usuário admin
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
        
        # Adicionar role se existir
        if hasattr(user, 'role'):
            user.role = 'admin'
            user.save()
            print(f"👤 Role definida: {user.role}")
        
        print("✅ Usuário admin criado com sucesso!")
        print(f"📧 Email: {email}")
        print(f"🔑 Senha: {password}")
        print(f"🆔 ID: {user.id}")
        print(f"🔐 Staff: {user.is_staff}")
        print(f"🔑 Superuser: {user.is_superuser}")
        print(f"✅ Ativo: {user.is_active}")
        
        # Verificar autenticação
        from django.contrib.auth import authenticate
        test_auth = authenticate(username=email, password=password)
        if test_auth:
            print("✅ Autenticação testada com sucesso!")
        else:
            # Tentar com username
            test_auth2 = authenticate(username=username, password=password)
            if test_auth2:
                print("✅ Autenticação com username funciona!")
            else:
                print("❌ Falha na autenticação")
        
        # Listar usuários
        print("\n👥 Usuários no sistema:")
        for u in User.objects.all():
            role_info = getattr(u, 'role', 'N/A')
            print(f"- Email: {u.email}, Username: {u.username}, Ativo: {u.is_active}, Role: {role_info}")
        
        print(f"\n🎯 CREDENCIAIS PARA LOGIN:")
        print(f"Email: {email}")
        print(f"Senha: {password}")
        print(f"URL Backend: http://localhost:8000")
        print(f"URL Frontend: http://localhost:4200 ou http://localhost:9000")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        return False

if __name__ == '__main__':
    success = create_admin_user()
    sys.exit(0 if success else 1)