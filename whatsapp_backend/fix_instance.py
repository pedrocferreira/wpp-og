#!/usr/bin/env python3
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from whatsapp.models import EvolutionConfig

def fix_instance():
    print("🔍 Verificando configurações existentes...")
    
    # Verificar configurações existentes
    configs = EvolutionConfig.objects.all()
    print(f"Total de configurações: {configs.count()}")
    
    for config in configs:
        print(f"  - ID: {config.id}, Instância: {config.instance_id}, Ativa: {config.is_active}")
    
    # Desativar todas as configurações
    EvolutionConfig.objects.all().update(is_active=False)
    print("🔕 Todas as configurações desativadas")
    
    # Criar/atualizar configuração correta para instância "Elo"
    config, created = EvolutionConfig.objects.get_or_create(
        instance_id='Elo',
        defaults={
            'api_key': '0891579bb8dda6a54deb403b0c01241c',
            'webhook_url': 'http://155.133.22.207:8000/api/whatsapp/webhook/evolution/',
            'is_active': True
        }
    )
    
    if not created:
        config.api_key = '0891579bb8dda6a54deb403b0c01241c'
        config.webhook_url = 'http://155.133.22.207:8000/api/whatsapp/webhook/evolution/'
        config.is_active = True
        config.save()
        print("🔄 Configuração atualizada!")
    else:
        print("✅ Nova configuração criada!")
    
    print(f"\n📋 Configuração final:")
    print(f"   Instância: {config.instance_id}")
    print(f"   API Key: {config.api_key[:20]}...")
    print(f"   Webhook: {config.webhook_url}")
    print(f"   Ativa: {config.is_active}")
    
    print("\n🎉 Configuração corrigida! A instância 'Elo' está ativa.")
    return config

if __name__ == "__main__":
    try:
        fix_instance()
    except Exception as e:
        print(f"❌ Erro: {e}")
        import traceback
        traceback.print_exc() 