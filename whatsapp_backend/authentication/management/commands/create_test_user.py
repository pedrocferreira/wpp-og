from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Cria usuário de teste para o sistema'

    def handle(self, *args, **options):
        # Verifica se já existe um usuário admin
        if User.objects.filter(email='admin@admin.com').exists():
            self.stdout.write(
                self.style.WARNING('Usuário admin já existe!')
            )
        else:
            # Cria usuário admin
            user = User.objects.create_user(
                username='admin',
                email='admin@admin.com',
                password='admin123',
                first_name='Admin',
                last_name='Sistema'
            )
            self.stdout.write(
                self.style.SUCCESS('Usuário admin criado com sucesso!')
            )

        self.stdout.write('\n=== CREDENCIAIS DE TESTE ===')
        self.stdout.write('Email: admin@admin.com')
        self.stdout.write('Senha: admin123') 