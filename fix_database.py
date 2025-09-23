#!/usr/bin/env python3

import os
import sys
import django

# Configurar Django
sys.path.append('/root/wpp-og/whatsapp_backend')
os.chdir('/root/wpp-og/whatsapp_backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')

# Forçar conexão PostgreSQL
os.environ['DB_HOST'] = 'localhost'
os.environ['DB_PORT'] = '5432'
os.environ['DB_NAME'] = 'whatsapp_db'
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = 'postgres123'

django.setup()

from django.core.management import execute_from_command_line
from django.db import connection
import traceback

def fix_database():
    print("🔧 Corrigindo problemas do banco de dados...")
    
    try:
        # 1. Aplicar migrações
        print("📊 Aplicando migrações...")
        execute_from_command_line(['manage.py', 'migrate', '--verbosity=1'])
        print("✅ Migrações aplicadas!")
        
        # 2. Verificar se a tabela EvolutionConfig existe
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'whatsapp_evolutionconfig'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
        if table_exists:
            print("✅ Tabela whatsapp_evolutionconfig existe!")
            
            # 3. Criar configuração Evolution
            from whatsapp.models import EvolutionConfig
            
            # Verificar se já existe configuração
            config = EvolutionConfig.objects.filter(is_active=True).first()
            
            if not config:
                print("📝 Criando configuração Evolution...")
                config = EvolutionConfig.objects.create(
                    instance_id="Elo",
                    api_key="0891579bb8dda6a54deb403b0c01241c",  # Da .env
                    webhook_url="http://155.133.22.207:8000/api/whatsapp/webhook/evolution/",
                    is_active=True
                )
                print(f"✅ Configuração criada: {config.instance_id}")
            else:
                print(f"✅ Configuração já existe: {config.instance_id}")
                # Atualizar URL do webhook
                config.webhook_url = "http://155.133.22.207:8000/api/whatsapp/webhook/evolution/"
                config.save()
                print("🔄 Webhook URL atualizada!")
            
        else:
            print("❌ Tabela whatsapp_evolutionconfig não foi criada!")
            
            # Listar tabelas existentes
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name LIKE 'whatsapp_%'
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                
            print("📋 Tabelas whatsapp existentes:")
            for table in tables:
                print(f"  - {table[0]}")
                
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = fix_database()
    print(f"\n{'✅ Sucesso!' if success else '❌ Falhou!'}")