from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Configura usuário admin do sistema'

    def handle(self, *args, **options):
        email = 'admin@admin.com'
        password = 'admin123'
        
        # Remove usuário se existir
        if User.objects.filter(email=email).exists():
            User.objects.filter(email=email).delete()
            self.stdout.write('Usuário admin anterior removido')
        
        # Cria novo usuário
        user = User.objects.create_user(
            username='admin',
            email=email,
            password=password,
            first_name='Admin',
            last_name='Sistema',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Usuário admin criado!')
        )
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Senha: {password}')
        self.stdout.write(f'ID: {user.id}') 