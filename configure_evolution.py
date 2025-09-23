#!/usr/bin/env python
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
sys.path.append('/app')
django.setup()

from whatsapp.models import EvolutionConfig

def configure_evolution():
    """Configura a Evolution API no banco de dados"""
    
    # Verificar se já existe configuração
    existing_config = EvolutionConfig.objects.filter(is_active=True).first()
    
    if existing_config:
        print(f"✅ Configuração ativa já existe: {existing_config.instance_id}")
        print(f"   Instância: {existing_config.instance_id}")
        print(f"   Webhook: {existing_config.webhook_url}")
        return existing_config
    
    # Criar nova configuração
    config = EvolutionConfig.objects.create(
        instance_id="Elo",
        api_key="067CD1A2E662-483F-A776-C977DED90692",
        webhook_url="http://og-trk.xyz/api/whatsapp/webhook/evolution/",
        is_active=True
    )
    
    print("🎉 Configuração da Evolution API criada com sucesso!")
    print(f"   ID: {config.id}")
    print(f"   Instância: {config.instance_id}")
    print(f"   API Key: {config.api_key[:20]}...")
    print(f"   Webhook: {config.webhook_url}")
    print(f"   Ativa: {config.is_active}")
    
    return config

if __name__ == "__main__":
    try:
        configure_evolution()
        print("\n✅ Configuração concluída! O WhatsApp deve funcionar agora.")
    except Exception as e:
        print(f"❌ Erro ao configurar: {e}") 