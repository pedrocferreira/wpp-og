from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Appointment, AppointmentReminder
from whatsapp.services import EvolutionAPIService
from whatsapp.ai_service import AIService
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_appointment_reminders():
    """
    Envia lembretes de consultas agendadas.
    """
    try:
        # Busca lembretes que devem ser enviados
        now = timezone.now()
        reminders = AppointmentReminder.objects.filter(
            sent=False,
            scheduled_for__lte=now,
            appointment__status__in=['scheduled', 'confirmed']
        ).select_related('appointment', 'appointment__client')

        evolution_service = EvolutionAPIService()
        ai_service = AIService()

        for reminder in reminders:
            try:
                # Gera mensagem personalizada
                message = ai_service.generate_reminder_message(reminder)
                
                # Envia mensagem via WhatsApp
                evolution_service.send_message(
                    reminder.appointment.client.whatsapp,
                    message
                )
                
                # Marca lembrete como enviado
                reminder.mark_as_sent()
                
                logger.info(f"Lembrete enviado com sucesso: {reminder}")
                
            except Exception as e:
                logger.error(f"Erro ao enviar lembrete {reminder.id}: {str(e)}")

    except Exception as e:
        logger.error(f"Erro ao processar lembretes: {str(e)}")
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