from django.core.management.base import BaseCommand
from django.utils import timezone
from appointments.models import Appointment, AppointmentReminder
from datetime import timedelta
import pytz


class Command(BaseCommand):
    help = 'Configura e testa o sistema de lembretes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--setup',
            action='store_true',
            help='Configura lembretes para agendamentos existentes'
        )
        parser.add_argument(
            '--test',
            action='store_true',
            help='Exibe mensagens de teste'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='Lista lembretes pendentes'
        )

    def handle(self, *args, **options):
        if options['setup']:
            self.setup_reminders()
        elif options['test']:
            self.test_messages()
        elif options['list']:
            self.list_reminders()
        else:
            self.stdout.write("Use --setup, --test ou --list")

    def setup_reminders(self):
        """Configura lembretes para agendamentos existentes"""
        self.stdout.write("🔧 Configurando sistema de lembretes...")
        
        # Busca agendamentos futuros sem lembretes
        future_appointments = Appointment.objects.filter(
            date_time__gt=timezone.now(),
            status='scheduled'
        )
        
        created_count = 0
        tz = pytz.timezone('America/Sao_Paulo')
        
        for appointment in future_appointments:
            # Deleta lembretes antigos para recriar
            AppointmentReminder.objects.filter(appointment=appointment).delete()
            
            # Lembrete 1 dia antes
            one_day_before = appointment.date_time - timedelta(days=1)
            if one_day_before.hour < 9:
                one_day_before = one_day_before.replace(hour=9, minute=0, second=0)
            
            if one_day_before > timezone.now():
                AppointmentReminder.objects.create(
                    appointment=appointment,
                    reminder_type='1_day',
                    scheduled_for=one_day_before,
                    sent=False
                )
                created_count += 1
            
            # Lembrete 2 horas antes
            two_hours_before = appointment.date_time - timedelta(hours=2)
            if two_hours_before > timezone.now():
                AppointmentReminder.objects.create(
                    appointment=appointment,
                    reminder_type='2_hours',
                    scheduled_for=two_hours_before,
                    sent=False
                )
                created_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"✅ Criados {created_count} lembretes para {future_appointments.count()} agendamentos!")
        )

    def test_messages(self):
        """Exibe mensagens de teste"""
        appointment = Appointment.objects.filter(
            date_time__gt=timezone.now(),
            status='scheduled'
        ).first()
        
        if not appointment:
            self.stdout.write("❌ Nenhum agendamento futuro encontrado para teste")
            return
        
        # Cria lembretes de exemplo
        one_day_reminder = AppointmentReminder(
            appointment=appointment,
            reminder_type='1_day',
            scheduled_for=appointment.date_time - timedelta(days=1)
        )
        
        two_hours_reminder = AppointmentReminder(
            appointment=appointment,
            reminder_type='2_hours',
            scheduled_for=appointment.date_time - timedelta(hours=2)
        )
        
        self.stdout.write("=" * 50)
        self.stdout.write(f"📅 CLIENTE: {appointment.client.name}")
        self.stdout.write(f"📞 WHATSAPP: {appointment.client.whatsapp}")
        self.stdout.write(f"🕐 CONSULTA: {appointment.date_time.strftime('%d/%m/%Y às %H:%M')}")
        self.stdout.write("=" * 50)
        
        self.stdout.write("\n🔔 LEMBRETE 1 DIA ANTES:")
        self.stdout.write(one_day_reminder.get_reminder_message())
        
        self.stdout.write("\n⏰ LEMBRETE 2 HORAS ANTES:")
        self.stdout.write(two_hours_reminder.get_reminder_message())

    def list_reminders(self):
        """Lista lembretes pendentes"""
        pending = AppointmentReminder.objects.filter(
            sent=False
        ).order_by('scheduled_for')
        
        self.stdout.write("📋 LEMBRETES PENDENTES:")
        self.stdout.write("=" * 60)
        
        if not pending:
            self.stdout.write("Nenhum lembrete pendente.")
            return
        
        for reminder in pending:
            now = timezone.now()
            if reminder.scheduled_for <= now:
                status = "🔴 DEVE SER ENVIADO AGORA"
            elif reminder.scheduled_for <= now + timedelta(hours=1):
                status = "🟡 PRÓXIMO ENVIO"
            else:
                status = "🟢 AGENDADO"
            
            self.stdout.write(
                f"{status} | {reminder.get_reminder_type_display()} | "
                f"{reminder.appointment.client.name} | "
                f"Envio: {reminder.scheduled_for.strftime('%d/%m %H:%M')} | "
                f"Consulta: {reminder.appointment.date_time.strftime('%d/%m %H:%M')}"
            )
        
        self.stdout.write(f"\n📊 Total: {pending.count()} lembretes pendentes") 