from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Appointment, AppointmentReminder, CustomReminderRequest
from whatsapp.services import EvolutionAPIService
from whatsapp.smart_ai_service import SmartAIService
from .reminder_service import ReminderService
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_appointment_reminders():
    """
    Tarefa Celery para enviar lembretes de agendamentos
    """
    try:
        # Busca lembretes pendentes
        now = timezone.now()
        reminders = AppointmentReminder.objects.filter(
            sent=False,
            scheduled_for__lte=now,
            appointment__status='scheduled'  # Só envia lembretes para consultas agendadas
        )
        
        evolution_service = EvolutionAPIService()
        
        for reminder in reminders:
            try:
                # Gera mensagem personalizada usando o método do modelo
                message = reminder.get_reminder_message()
                
                # Envia o lembrete
                result = evolution_service.send_message(
                    reminder.appointment.client.whatsapp,
                    message
                )
                
                # Marca como enviado com a resposta da API
                reminder.mark_as_sent(response=str(result) if result else 'Enviado sem resposta')
                
                logger.info("Lembrete enviado com sucesso - %s para %s", 
                           reminder.get_reminder_type_display(), 
                           reminder.appointment.client.whatsapp)
                
            except Exception as e:
                logger.error("Erro ao enviar lembrete %s: %s", reminder.id, str(e))
                continue
                
    except Exception as e:
        logger.error("Erro ao processar lembretes: %s", str(e))
        raise

@shared_task
def send_custom_reminders():
    """
    Tarefa Celery para enviar lembretes personalizados
    """
    try:
        reminder_service = ReminderService()
        reminder_service.send_custom_reminders()
        
    except Exception as e:
        logger.error("Erro ao processar lembretes personalizados: %s", str(e))
        raise

@shared_task
def send_followup_messages():
    """
    Envia mensagens de acompanhamento após as consultas
    """
    # Busca consultas completadas nas últimas 24 horas
    yesterday = timezone.now() - timedelta(days=1)
    completed = Appointment.objects.filter(
        date_time__gte=yesterday,
        date_time__lt=timezone.now(),
        status='completed'
    )

    evolution_service = EvolutionAPIService()

    for appointment in completed:
        try:
            message = (
                f"Olá {appointment.client.name}! Esperamos que sua consulta tenha sido proveitosa. "
                "Gostaríamos de saber como foi sua experiência. "
                "Se precisar agendar uma nova consulta, estamos à disposição."
            )

            evolution_service.send_message(
                appointment.client.whatsapp,
                message
            )

        except Exception as e:
            print(f"Erro ao enviar mensagem de acompanhamento para consulta {appointment.id}: {str(e)}")

@shared_task
def create_missing_reminders():
    """
    Cria lembretes para agendamentos futuros que não possuem lembretes configurados
    """
    try:
        from datetime import timedelta
        
        # Busca agendamentos futuros sem lembretes
        future_appointments = Appointment.objects.filter(
            date_time__gt=timezone.now(),
            status='scheduled'
        )
        
        created_count = 0
        
        for appointment in future_appointments:
            # Verifica se já tem lembretes
            existing_reminders = AppointmentReminder.objects.filter(
                appointment=appointment
            ).count()
            
            if existing_reminders == 0:
                # Cria lembrete 1 dia antes
                one_day_before = appointment.date_time - timedelta(days=1)
                # Ajusta para 9h se for muito cedo
                if one_day_before.hour < 9:
                    one_day_before = one_day_before.replace(hour=9, minute=0, second=0)
                
                # Só cria se não for no passado
                if one_day_before > timezone.now():
                    AppointmentReminder.objects.get_or_create(
                        appointment=appointment,
                        reminder_type='1_day',
                        defaults={
                            'scheduled_for': one_day_before,
                            'sent': False
                        }
                    )
                    created_count += 1
                
                # Cria lembrete 2 horas antes
                two_hours_before = appointment.date_time - timedelta(hours=2)
                
                # Só cria se não for no passado
                if two_hours_before > timezone.now():
                    AppointmentReminder.objects.get_or_create(
                        appointment=appointment,
                        reminder_type='2_hours',
                        defaults={
                            'scheduled_for': two_hours_before,
                            'sent': False
                        }
                    )
                    created_count += 1
        
        logger.info(f"Criados {created_count} lembretes para agendamentos existentes")
        
    except Exception as e:
        logger.error("Erro ao criar lembretes faltantes: %s", str(e))
        raise

@shared_task
def check_expired_appointments():
    """
    Verifica e atualiza o status de consultas expiradas
    """
    # Busca consultas agendadas que já passaram
    expired = Appointment.objects.filter(
        date_time__lt=timezone.now(),
        status='scheduled'
    )

    for appointment in expired:
        appointment.status = 'completed'
        appointment.save()
        
    logger.info(f"Atualizadas {expired.count()} consultas expiradas") 