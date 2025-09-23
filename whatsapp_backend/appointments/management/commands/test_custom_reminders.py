from django.core.management.base import BaseCommand
from appointments.reminder_service import ReminderService
from authentication.models import Client
from appointments.models import Appointment
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Testa o sistema de lembretes personalizados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-message',
            type=str,
            help='Mensagem para testar detecção de lembretes'
        )

    def handle(self, *args, **options):
        self.stdout.write("🧪 Testando sistema de lembretes personalizados...")
        
        # Teste 1: Detecção de pedidos de lembretes
        self.test_reminder_detection()
        
        # Teste 2: Criação de lembretes personalizados
        self.test_reminder_creation()
        
        # Teste 3: Mensagens personalizadas
        self.test_custom_messages()
        
        # Teste 4: Teste com mensagem específica
        if options['test_message']:
            self.test_specific_message(options['test_message'])

    def test_reminder_detection(self):
        """Testa a detecção de pedidos de lembretes"""
        self.stdout.write("\n📋 Teste 1: Detecção de pedidos de lembretes")
        
        reminder_service = ReminderService()
        test_messages = [
            "me avisa 2 horas antes",
            "me avisa 1 dia antes", 
            "me avisa 1 semana antes",
            "lembra 30 minutos antes",
            "avisa 3 horas antes",
            "me lembra 1 dia antes",
            "oi, tudo bem?",  # Não deve detectar
            "quero agendar",  # Não deve detectar
        ]
        
        for message in test_messages:
            is_request, timing, timing_minutes, appointment = reminder_service.detect_reminder_request(
                message, "5511999999999"
            )
            
            if is_request:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ '{message}' → {timing} ({timing_minutes} minutos)")
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f"❌ '{message}' → Não detectado")
                )

    def test_reminder_creation(self):
        """Testa a criação de lembretes personalizados"""
        self.stdout.write("\n📋 Teste 2: Criação de lembretes personalizados")
        
        # Criar cliente de teste
        client, created = Client.objects.get_or_create(
            whatsapp="5511999999999",
            defaults={'name': 'Cliente Teste'}
        )
        
        # Criar agendamento de teste (amanhã às 14h)
        tomorrow = timezone.now() + timedelta(days=1)
        appointment_datetime = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        appointment, created = Appointment.objects.get_or_create(
            client=client,
            date_time=appointment_datetime,
            defaults={
                'status': 'scheduled',
                'source': 'test',
                'description': 'Consulta de teste'
            }
        )
        
        reminder_service = ReminderService()
        
        # Testar criação de lembrete 2 horas antes
        success, result = reminder_service.create_custom_reminder(
            client=client,
            appointment=appointment,
            timing="2 horas antes",
            timing_minutes=120,
            request_text="me avisa 2 horas antes"
        )
        
        if success:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Lembrete criado com sucesso: {result}")
            )
        else:
            self.stdout.write(
                self.style.ERROR(f"❌ Erro ao criar lembrete: {result}")
            )

    def test_custom_messages(self):
        """Testa a geração de mensagens personalizadas"""
        self.stdout.write("\n📋 Teste 3: Mensagens personalizadas")
        
        reminder_service = ReminderService()
        
        # Data de teste (amanhã às 14h)
        tomorrow = timezone.now() + timedelta(days=1)
        appointment_datetime = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
        
        test_timings = [
            "2 horas antes",
            "1 dia antes", 
            "1 semana antes",
            "30 minutos antes"
        ]
        
        for timing in test_timings:
            message = reminder_service._generate_custom_reminder_message(
                "Cliente Teste",
                appointment_datetime,
                timing
            )
            
            self.stdout.write(f"\n📝 {timing}:")
            self.stdout.write(f"   {message[:100]}...")

    def test_specific_message(self, message):
        """Testa uma mensagem específica"""
        self.stdout.write(f"\n📋 Teste 4: Mensagem específica: '{message}'")
        
        reminder_service = ReminderService()
        is_request, timing, timing_minutes, appointment = reminder_service.detect_reminder_request(
            message, "5511999999999"
        )
        
        if is_request:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Detectado: {timing} ({timing_minutes} minutos)")
            )
            
            if appointment:
                self.stdout.write(f"   📅 Consulta: {appointment.date_time.strftime('%d/%m às %H:%M')}")
            else:
                self.stdout.write("   ⚠️  Nenhuma consulta futura encontrada")
        else:
            self.stdout.write(
                self.style.WARNING("❌ Não detectado como pedido de lembrete")
            ) 