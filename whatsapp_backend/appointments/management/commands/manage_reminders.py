from django.core.management.base import BaseCommand
from django.utils import timezone
from appointments.models import Appointment, AppointmentReminder
from appointments.tasks import create_missing_reminders, send_appointment_reminders
from datetime import timedelta


class Command(BaseCommand):
    help = 'Gerencia lembretes de agendamentos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            choices=['create', 'send', 'list', 'test'],
            required=True,
            help='Ação a ser executada'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força o envio de lembretes mesmo que não seja o horário'
        )

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'create':
            self.create_reminders()
        elif action == 'send':
            self.send_reminders(force=options.get('force', False))
        elif action == 'list':
            self.list_reminders()
        elif action == 'test':
            self.test_reminder_messages()

    def create_reminders(self):
        """Cria lembretes para agendamentos que não possuem"""
        self.stdout.write("Criando lembretes para agendamentos existentes...")
        
        try:
            create_missing_reminders()
            self.stdout.write(
                self.style.SUCCESS("Lembretes criados com sucesso!")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Erro ao criar lembretes: {e}")
            )

    def send_reminders(self, force=False):
        """Envia lembretes pendentes"""
        now = timezone.now()
        
        if force:
            # Se forçado, envia todos os lembretes pendentes
            reminders = AppointmentReminder.objects.filter(
                sent=False,
                appointment__status='scheduled'
            )
            self.stdout.write("Enviando TODOS os lembretes pendentes (FORÇADO)...")
        else:
            # Envia apenas lembretes que devem ser enviados agora
            reminders = AppointmentReminder.objects.filter(
                sent=False,
                scheduled_for__lte=now,
                appointment__status='scheduled'
            )
            self.stdout.write("Enviando lembretes programados para agora...")
        
        sent_count = 0
        for reminder in reminders:
            try:
                send_appointment_reminders()
                sent_count += 1
                self.stdout.write(
                    f"✓ {reminder.get_reminder_type_display()} - {reminder.appointment.client.name}"
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Erro ao enviar para {reminder.appointment.client.name}: {e}")
                )
        
        self.stdout.write(
            self.style.SUCCESS(f"Enviados {sent_count} lembretes!")
        )

    def list_reminders(self):
        """Lista todos os lembretes"""
        self.stdout.write("=== LEMBRETES PENDENTES ===")
        
        pending = AppointmentReminder.objects.filter(sent=False).order_by('scheduled_for')
        
        if not pending:
            self.stdout.write("Nenhum lembrete pendente.")
            return
        
        for reminder in pending:
            status = "⏰ AGENDADO" if reminder.scheduled_for > timezone.now() else "⚠️ ATRASADO"
            
            self.stdout.write(
                f"{status} | {reminder.get_reminder_type_display()} | "
                f"{reminder.appointment.client.name} | "
                f"{reminder.scheduled_for.strftime('%d/%m/%Y %H:%M')} | "
                f"Consulta: {reminder.appointment.date_time.strftime('%d/%m/%Y %H:%M')}"
            )
        
        self.stdout.write(f"\nTotal: {pending.count()} lembretes pendentes")

    def test_reminder_messages(self):
        """Mostra exemplos de mensagens de lembrete"""
        self.stdout.write("=== TESTE DE MENSAGENS ===")
        
        # Busca um agendamento para teste
        appointment = Appointment.objects.filter(
            date_time__gt=timezone.now(),
            status='scheduled'
        ).first()
        
        if not appointment:
            self.stdout.write("Nenhum agendamento futuro encontrado para teste.")
            return
        
        # Cria lembretes de exemplo (sem salvar)
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
        
        self.stdout.write(f"Cliente: {appointment.client.name}")
        self.stdout.write(f"Consulta: {appointment.date_time.strftime('%d/%m/%Y %H:%M')}")
        self.stdout.write("")
        
        self.stdout.write("--- LEMBRETE 1 DIA ANTES ---")
        self.stdout.write(one_day_reminder.get_reminder_message())
        self.stdout.write("")
        
        self.stdout.write("--- LEMBRETE 2 HORAS ANTES ---")
        self.stdout.write(two_hours_reminder.get_reminder_message()) 