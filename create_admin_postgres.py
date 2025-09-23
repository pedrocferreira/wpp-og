#!/usr/bin/env python3

import os
import sys
import django

# Configurar o caminho do Django
sys.path.append('/root/wpp-og/whatsapp_backend')
os.chdir('/root/wpp-og/whatsapp_backend')

# Configurar Django para usar PostgreSQL (configuração padrão)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')

# Configurar para conectar ao PostgreSQL via localhost
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'whatsapp_db'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'postgres123'

django.setup()

from django.contrib.auth import get_user_model
from django.db import connection

def create_admin_user():
    User = get_user_model()
    
    # Credenciais do admin
    email = 'admin@admin.com'
    password = 'admin1234'
    username = 'admin'
    
    print("🔧 Criando usuário admin no PostgreSQL...")
    print(f"📊 Banco: {connection.settings_dict['NAME']}")
    print(f"🏠 Host: {connection.settings_dict['HOST']}")
    
    try:
        # Verificar conexão
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"🐘 PostgreSQL: {version[0]}")
        
        # Limpar usuários admin existentes
        deleted_count = User.objects.filter(email__in=[email, 'admin@example.com']).delete()[0]
        if deleted_count > 0:
            print(f"🗑️ {deleted_count} usuários com email admin removidos")
        
        deleted_count2 = User.objects.filter(username=username).delete()[0]
        if deleted_count2 > 0:
            print(f"🗑️ {deleted_count2} usuários com username '{username}' removidos")
        
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
        
        print("✅ Usuário admin criado com sucesso no PostgreSQL!")
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
            print("✅ Autenticação por email testada com sucesso!")
        else:
            # Tentar com username
            test_auth2 = authenticate(username=username, password=password)
            if test_auth2:
                print("✅ Autenticação por username funciona!")
            else:
                print("❌ Falha na autenticação")
        
        # Listar usuários
        print("\n👥 Usuários no PostgreSQL:")
        for u in User.objects.all():
            role_info = getattr(u, 'role', 'N/A')
            print(f"- Email: {u.email}, Username: {u.username}, Ativo: {u.is_active}, Role: {role_info}")
        
        print(f"\n🎯 CREDENCIAIS PARA LOGIN:")
        print(f"Email: {email}")
        print(f"Senha: {password}")
        print(f"Endpoint: http://localhost:8000/api/auth/login/")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar usuário: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = create_admin_user()
    sys.exit(0 if success else 1)