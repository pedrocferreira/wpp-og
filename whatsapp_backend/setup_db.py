#!/usr/bin/env python3
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from whatsapp.models import EvolutionConfig

def setup_database():
    """Configura a instância Evolution API no banco de dados"""
    
    print("🔍 Verificando configurações existentes...")
    
    # Verificar configurações existentes
    configs = EvolutionConfig.objects.all()
    print(f"Total de configurações: {configs.count()}")
    
    for config in configs:
        print(f"  - ID: {config.id}, Instância: {config.instance_id}, Ativa: {config.is_active}")
    
    # Criar ou atualizar configuração para instância "Elo"
    config, created = EvolutionConfig.objects.get_or_create(
        instance_id='Elo',
        defaults={
            'api_key': '0891579bb8dda6a54deb403b0c01241c',
            'webhook_url': 'http://og-trk.xyz/api/whatsapp/webhook/evolution/',
            'is_active': True
        }
    )
    
    if created:
        print("✅ Nova configuração criada para instância 'Elo'!")
    else:
        print("✅ Configuração já existia para instância 'Elo'!")
        # Atualizar se necessário
        config.api_key = '0891579bb8dda6a54deb403b0c01241c'
        config.webhook_url = 'http://og-trk.xyz/api/whatsapp/webhook/evolution/'
        config.is_active = True
        config.save()
        print("🔄 Configuração atualizada!")
    
    print(f"\n📋 Configuração final:")
    print(f"   Instância: {config.instance_id}")
    print(f"   API Key: {config.api_key[:20]}...")
    print(f"   Webhook: {config.webhook_url}")
    print(f"   Ativa: {config.is_active}")
    
    # Desativar outras configurações
    other_configs = EvolutionConfig.objects.exclude(id=config.id)
    if other_configs.exists():
        other_configs.update(is_active=False)
        print(f"🔕 Desativadas {other_configs.count()} outras configurações")
    
    print("\n🎉 Configuração do banco de dados concluída!")
    return config

if __name__ == "__main__":
    try:
        setup_database()
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc() 