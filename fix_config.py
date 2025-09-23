from whatsapp.models import EvolutionConfig

# Verificar configurações existentes
configs = EvolutionConfig.objects.all()
print('=== Configurações Existentes ===')
for config in configs:
    print(f'ID: {config.id} | Instância: {config.instance_id} | Ativa: {config.is_active}')

# Desativar todas as configurações
EvolutionConfig.objects.all().update(is_active=False)

# Criar/atualizar configuração correta
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

print('=== Configuração Corrigida ===')
print(f'Instância: {config.instance_id}')
print(f'API Key: {config.api_key[:20]}...')
print(f'Webhook: {config.webhook_url}')
print(f'Ativa: {config.is_active}')
print('✅ Configuração corrigida! Agora a instância Elo está ativa.') 