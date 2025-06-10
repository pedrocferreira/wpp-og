from django.core.management.base import BaseCommand
from django.conf import settings
from whatsapp.models import EvolutionConfig
from whatsapp.evolution_service import EvolutionService

class Command(BaseCommand):
    help = 'Configura a integração com o Evolution API'

    def handle(self, *args, **options):
        # Criar ou atualizar configuração
        webhook_url = f"http://{settings.ALLOWED_HOSTS[0]}/api/whatsapp/webhook/evolution/"
        
        config, created = EvolutionConfig.objects.update_or_create(
            instance_id=settings.EVOLUTION_INSTANCE_ID,
            defaults={
                'api_key': settings.EVOLUTION_API_KEY,
                'webhook_url': webhook_url,
                'is_active': True
            }
        )

        self.stdout.write(self.style.SUCCESS(f'{"Criada" if created else "Atualizada"} configuração do Evolution API'))

        # Configurar webhook
        try:
            service = EvolutionService()
            service.setup_webhook()
            self.stdout.write(self.style.SUCCESS('Webhook configurado com sucesso'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Erro ao configurar webhook: {str(e)}')) 