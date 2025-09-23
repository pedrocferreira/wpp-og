#!/usr/bin/env python3

import os
import sys

# Script para criar usuário admin via shell
shell_commands = '''
import os
os.environ["DB_HOST"] = "localhost"

from django.contrib.auth import get_user_model
User = get_user_model()

# Credenciais do admin
email = "admin@admin.com"
password = "admin1234"
username = "admin"

print("🔧 Criando usuário admin...")

# Tentar criar usuário
try:
    # Verificar se usuário já existe
    if User.objects.filter(email=email).exists():
        print("🗑️ Removendo usuário existente...")
        User.objects.filter(email=email).delete()
    
    if User.objects.filter(username=username).exists():
        print("🗑️ Removendo username existente...")
        User.objects.filter(username=username).delete()
    
    # Criar novo usuário
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name="Admin",
        last_name="Sistema",
        is_staff=True,
        is_superuser=True,
        is_active=True
    )
    
    # Definir role se existir
    if hasattr(user, "role"):
        user.role = "admin"
        user.save()
    
    print("✅ Usuário admin criado com sucesso!")
    print(f"📧 Email: {email}")
    print(f"🔑 Senha: {password}")
    print(f"🆔 ID: {user.id}")
    
    # Teste de autenticação
    from django.contrib.auth import authenticate
    test_user = authenticate(username=email, password=password)
    if test_user:
        print("✅ Autenticação funcionando!")
    else:
        print("❌ Problema na autenticação")
        
except Exception as e:
    print(f"❌ Erro: {e}")

# Listar usuários
print("\\n👥 Usuários no sistema:")
for u in User.objects.all():
    print(f"- {u.email} ({u.username}) - Ativo: {u.is_active}")

print("\\n🎯 Use essas credenciais para login:")
print(f"Email: {email}")
print(f"Senha: {password}")
'''

# Escrever comandos em arquivo temporário
with open('/tmp/create_admin.py', 'w') as f:
    f.write(shell_commands)

print("Script criado. Execute:")
print("cd /root/wpp-og/whatsapp_backend")  
print("source ../venv/bin/activate")
print("DB_HOST=localhost python3 manage.py shell < /tmp/create_admin.py")