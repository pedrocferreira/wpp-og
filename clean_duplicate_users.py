#!/usr/bin/env python
import os
import sys
import django

# Configurar o Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
sys.path.append('/root/wpp-og/whatsapp_backend')
django.setup()

from authentication.models import User

def clean_duplicate_users():
    print("🔍 Verificando usuários duplicados...")
    
    # Buscar todos os usuários admin
    admin_users = User.objects.filter(is_superuser=True).order_by('id')
    
    print(f"📊 Encontrados {admin_users.count()} usuários admin:")
    for user in admin_users:
        print(f"  - ID: {user.id}, Username: {user.username}, Email: {user.email}")
    
    if admin_users.count() > 1:
        print("\n🧹 Removendo usuários duplicados...")
        
        # Manter apenas o primeiro usuário admin
        first_admin = admin_users.first()
        duplicate_admins = admin_users.exclude(id=first_admin.id)
        
        print(f"✅ Mantendo: ID {first_admin.id} - {first_admin.username} ({first_admin.email})")
        
        for duplicate in duplicate_admins:
            print(f"❌ Removendo: ID {duplicate.id} - {duplicate.username} ({duplicate.email})")
            duplicate.delete()
        
        print(f"\n🎉 Limpeza concluída! Agora há apenas 1 usuário admin.")
    else:
        print("\n✅ Não há usuários duplicados.")
    
    # Verificar resultado final
    final_count = User.objects.filter(is_superuser=True).count()
    print(f"\n📈 Total de usuários admin após limpeza: {final_count}")

if __name__ == "__main__":
    clean_duplicate_users() 