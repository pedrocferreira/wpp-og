import re
from datetime import datetime, timedelta
from django.utils import timezone
from .models import Appointment, AppointmentReminder, CustomReminderRequest
from authentication.models import Client
import logging

logger = logging.getLogger(__name__)

class ReminderService:
    """Serviço para gerenciar lembretes personalizados"""
    
    def __init__(self):
        self.timezone = timezone.get_current_timezone()
    
    def detect_reminder_request(self, message_text, client_whatsapp):
        """
        Detecta se a mensagem contém um pedido de lembrete personalizado
        Retorna (is_request, timing, appointment) ou (False, None, None)
        """
        message_lower = message_text.lower()
        
        # Padrões para detectar pedidos de lembretes
        reminder_patterns = [
            r'me avisa\s+(\d+)\s+(?:hora|horas?)\s+antes',
            r'me avisa\s+(\d+)\s+(?:dia|dias?)\s+antes',
            r'me avisa\s+(\d+)\s+(?:semana|semanas?)\s+antes',
            r'me avisa\s+(\d+)\s+(?:minuto|minutos?)\s+antes',
            r'avisa\s+(\d+)\s+(?:hora|horas?)\s+antes',
            r'avisa\s+(\d+)\s+(?:dia|dias?)\s+antes',
            r'avisa\s+(\d+)\s+(?:semana|semanas?)\s+antes',
            r'avisa\s+(\d+)\s+(?:minuto|minutos?)\s+antes',
            r'lembra\s+(\d+)\s+(?:hora|horas?)\s+antes',
            r'lembra\s+(\d+)\s+(?:dia|dias?)\s+antes',
            r'lembra\s+(\d+)\s+(?:semana|semanas?)\s+antes',
            r'lembra\s+(\d+)\s+(?:minuto|minutos?)\s+antes',
            r'me lembra\s+(\d+)\s+(?:hora|horas?)\s+antes',
            r'me lembra\s+(\d+)\s+(?:dia|dias?)\s+antes',
            r'me lembra\s+(\d+)\s+(?:semana|semanas?)\s+antes',
            r'me lembra\s+(\d+)\s+(?:minuto|minutos?)\s+antes',
        ]
        
        for pattern in reminder_patterns:
            match = re.search(pattern, message_lower)
            if match:
                number = int(match.group(1))
                
                # Determinar o tipo de timing
                if 'hora' in pattern:
                    timing = f"{number} hora{'s' if number > 1 else ''} antes"
                    timing_minutes = number * 60
                elif 'dia' in pattern:
                    timing = f"{number} dia{'s' if number > 1 else ''} antes"
                    timing_minutes = number * 24 * 60
                elif 'semana' in pattern:
                    timing = f"{number} semana{'s' if number > 1 else ''} antes"
                    timing_minutes = number * 7 * 24 * 60
                elif 'minuto' in pattern:
                    timing = f"{number} minuto{'s' if number > 1 else ''} antes"
                    timing_minutes = number
                else:
                    continue
                
                # Buscar próxima consulta do cliente
                try:
                    client = Client.objects.get(whatsapp=client_whatsapp)
                    next_appointment = Appointment.objects.filter(
                        client=client,
                        date_time__gt=timezone.now(),
                        status='scheduled'
                    ).order_by('date_time').first()
                    
                    if next_appointment:
                        return True, timing, timing_minutes, next_appointment
                    else:
                        return True, timing, timing_minutes, None
                        
                except Client.DoesNotExist:
                    return False, None, None, None
        
        return False, None, None, None
    
    def create_custom_reminder(self, client, appointment, timing, timing_minutes, request_text):
        """
        Cria um lembrete personalizado baseado no pedido do cliente
        """
        try:
            # Calcular quando o lembrete deve ser enviado
            reminder_time = appointment.date_time - timedelta(minutes=timing_minutes)
            
            # Só criar se o lembrete for no futuro
            if reminder_time <= timezone.now():
                return False, "O lembrete seria no passado"
            
            # Gerar mensagem personalizada
            message = self._generate_custom_reminder_message(
                client.name, 
                appointment.date_time, 
                timing
            )
            
            # Criar o lembrete personalizado
            custom_reminder = CustomReminderRequest.objects.create(
                client=client,
                appointment=appointment,
                request_text=request_text,
                reminder_timing=timing,
                scheduled_for=reminder_time,
                message=message
            )
            
            # Também criar no sistema de lembretes padrão
            AppointmentReminder.objects.get_or_create(
                appointment=appointment,
                reminder_type='custom',
                defaults={
                    'scheduled_for': reminder_time,
                    'custom_message': message,
                    'custom_timing': timing,
                    'sent': False
                }
            )
            
            logger.info(f"Lembrete personalizado criado: {timing} para {client.name}")
            return True, custom_reminder
            
        except Exception as e:
            logger.error(f"Erro ao criar lembrete personalizado: {e}")
            return False, str(e)
    
    def _generate_custom_reminder_message(self, client_name, appointment_datetime, timing):
        """
        Gera mensagem personalizada para o lembrete
        """
        date_str = appointment_datetime.strftime('%d/%m/%Y')
        time_str = appointment_datetime.strftime('%H:%M')
        
        # Determina o dia da semana em português
        weekdays = ['segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado', 'domingo']
        weekday = weekdays[appointment_datetime.weekday()]
        
        # Determina se é hoje, amanhã ou outro dia
        today = timezone.now().date()
        appointment_date = appointment_datetime.date()
        
        if appointment_date == today:
            day_ref = "hoje"
        elif appointment_date == today + timedelta(days=1):
            day_ref = "amanhã"
        else:
            day_ref = f"na {weekday} ({date_str})"
        
        # Mensagem baseada no tipo de timing
        if 'hora' in timing:
            if '1 hora' in timing:
                message = (
                    f"Oi, {client_name}! ⏰\n\n"
                    f"Sua consulta é daqui a 1 hora (às {time_str}).\n\n"
                    f"Já está se preparando pra vir? Se houver algum imprevisto, me avise o quanto antes!\n\n"
                    f"Te esperamos aqui! 😊"
                )
            else:
                hours = timing.split()[0]
                message = (
                    f"Oi, {client_name}! ⏰\n\n"
                    f"Sua consulta é daqui a {hours} horas (às {time_str}).\n\n"
                    f"Já está se preparando pra vir? Se houver algum imprevisto, me avise o quanto antes!\n\n"
                    f"Te esperamos aqui! 😊"
                )
        elif 'dia' in timing:
            if '1 dia' in timing:
                message = (
                    f"Oi, {client_name}! 😊\n\n"
                    f"Só lembrando que você tem consulta agendada amanhã, {weekday} ({date_str}) às {time_str}.\n\n"
                    f"Se não puder vir, me avise com antecedência, tá? Assim posso reagendar pra outro horário que funcione melhor pra você!\n\n"
                    f"Até amanhã! 💙"
                )
            else:
                days = timing.split()[0]
                message = (
                    f"Oi, {client_name}! 📅\n\n"
                    f"Só lembrando que você tem consulta agendada em {days} dias, {weekday} ({date_str}) às {time_str}.\n\n"
                    f"Se não puder vir, me avise com antecedência, tá? Assim posso reagendar pra outro horário que funcione melhor pra você!\n\n"
                    f"Até lá! 💙"
                )
        elif 'semana' in timing:
            if '1 semana' in timing:
                message = (
                    f"Oi, {client_name}! 📅\n\n"
                    f"Só lembrando que você tem consulta agendada na próxima semana, {weekday} ({date_str}) às {time_str}.\n\n"
                    f"Se não puder vir, me avise com antecedência, tá? Assim posso reagendar pra outro horário que funcione melhor pra você!\n\n"
                    f"Até lá! 💙"
                )
            else:
                weeks = timing.split()[0]
                message = (
                    f"Oi, {client_name}! 📅\n\n"
                    f"Só lembrando que você tem consulta agendada em {weeks} semanas, {weekday} ({date_str}) às {time_str}.\n\n"
                    f"Se não puder vir, me avise com antecedência, tá? Assim posso reagendar pra outro horário que funcione melhor pra você!\n\n"
                    f"Até lá! 💙"
                )
        else:
            # Mensagem genérica
            message = (
                f"Oi, {client_name}! 📅\n\n"
                f"Lembrando da sua consulta {day_ref} às {time_str}.\n\n"
                f"Se não puder vir, me avise com antecedência!\n\n"
                f"Qualquer dúvida, me chame! 😊"
            )
        
        return message
    
    def send_custom_reminders(self):
        """
        Envia lembretes personalizados pendentes
        """
        try:
            from whatsapp.services import EvolutionAPIService
            
            now = timezone.now()
            pending_reminders = CustomReminderRequest.objects.filter(
                sent=False,
                scheduled_for__lte=now
            )
            
            evolution_service = EvolutionAPIService()
            
            for reminder in pending_reminders:
                try:
                    # Envia o lembrete
                    result = evolution_service.send_message(
                        reminder.client.whatsapp,
                        reminder.message
                    )
                    
                    # Marca como enviado
                    reminder.mark_as_sent()
                    
                    logger.info(f"Lembrete personalizado enviado: {reminder.reminder_timing} para {reminder.client.name}")
                    
                except Exception as e:
                    logger.error(f"Erro ao enviar lembrete personalizado {reminder.id}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erro ao processar lembretes personalizados: {str(e)}")
            raise 