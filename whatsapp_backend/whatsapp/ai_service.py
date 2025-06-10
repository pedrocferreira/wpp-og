import openai
from django.conf import settings
import logging
from datetime import datetime, timedelta
import json
from appointments.models import Appointment, AppointmentReminder
from django.utils import timezone
import pytz

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        openai.api_key = settings.OPENAI_API_KEY
        self.system_prompt = f"""Você é a {settings.AI_ASSISTANT_NAME}, uma assistente virtual para agendamento de consultas.
        Seja cordial e profissional, sempre se apresentando como {settings.AI_ASSISTANT_NAME}. 
        
        Suas principais funções são:
        1. Agendar novas consultas
        2. Remarcar consultas existentes
        3. Cancelar consultas
        4. Tirar dúvidas sobre horários disponíveis
        5. Confirmar consultas agendadas
        
        Ao agendar consultas, você deve:
        - Coletar data e hora desejadas
        - Verificar disponibilidade
        - Confirmar os dados com o cliente
        - Gerar uma resposta estruturada em JSON com os dados do agendamento
        
        Formato da resposta JSON para agendamentos:
        {
            "intent": "schedule_appointment",
            "data": {
                "date": "YYYY-MM-DD",
                "time": "HH:MM",
                "description": "Descrição da consulta",
                "action": "schedule|reschedule|cancel|confirm"
            }
        }
        
        Mantenha as respostas concisas e objetivas, sempre com um tom amigável e prestativo."""

    def process_message(self, message_content, context=None):
        """
        Processa a mensagem do usuário e retorna uma resposta apropriada.
        """
        try:
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]

            if context:
                messages.append({
                    "role": "system", 
                    "content": f"Contexto do cliente: {json.dumps(context)}"
                })

            messages.append({"role": "user", "content": message_content})

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                temperature=0.7,
                max_tokens=300
            )

            response_text = response.choices[0].message.content
            
            # Tenta extrair JSON da resposta
            try:
                # Procura por um bloco JSON na resposta
                import re
                json_match = re.search(r'{.*}', response_text, re.DOTALL)
                if json_match:
                    json_data = json.loads(json_match.group())
                    if json_data.get('intent') == 'schedule_appointment':
                        # Processa o agendamento
                        self._process_appointment(json_data['data'], context)
                else:
                    json_data = {"intent": "conversation"}
            except Exception as e:
                logger.error(f"Erro ao processar JSON da resposta: {str(e)}")
                json_data = {"intent": "conversation"}

            return {
                'response_text': response_text,
                'confidence_score': response.choices[0].finish_reason == 'stop' and 1.0 or 0.8,
                'intent_detected': json_data.get('intent', 'conversation')
            }

        except Exception as e:
            logger.error(f"Erro no serviço de IA: {str(e)}")
            return {
                'response_text': "Desculpe, tive um problema ao processar sua mensagem. Por favor, tente novamente.",
                'confidence_score': 0.0,
                'intent_detected': 'error'
            }

    def _process_appointment(self, appointment_data, context):
        """
        Processa os dados de agendamento e cria/atualiza registros no banco.
        """
        try:
            # Converte data e hora para datetime
            date_str = appointment_data['date']
            time_str = appointment_data['time']
            date_time = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
            
            # Converte para timezone aware
            tz = pytz.timezone(settings.TIME_ZONE)
            date_time = tz.localize(date_time)

            if appointment_data['action'] == 'schedule':
                # Cria novo agendamento
                appointment = Appointment.objects.create(
                    client_id=context['client_id'],
                    date_time=date_time,
                    description=appointment_data['description'],
                    status='scheduled'
                )
                
                # Cria lembretes
                self._create_reminders(appointment)
                
            elif appointment_data['action'] == 'reschedule':
                # Atualiza agendamento existente
                appointment = Appointment.objects.get(
                    client_id=context['client_id'],
                    date_time__gte=timezone.now(),
                    status='scheduled'
                )
                appointment.date_time = date_time
                appointment.save()
                
                # Atualiza lembretes
                self._create_reminders(appointment)
                
            elif appointment_data['action'] == 'cancel':
                # Cancela agendamento
                appointment = Appointment.objects.get(
                    client_id=context['client_id'],
                    date_time__gte=timezone.now(),
                    status='scheduled'
                )
                appointment.status = 'cancelled'
                appointment.save()
                
            elif appointment_data['action'] == 'confirm':
                # Confirma agendamento
                appointment = Appointment.objects.get(
                    client_id=context['client_id'],
                    date_time__gte=timezone.now(),
                    status='scheduled'
                )
                appointment.status = 'confirmed'
                appointment.save()

        except Exception as e:
            logger.error(f"Erro ao processar agendamento: {str(e)}")
            raise

    def _create_reminders(self, appointment):
        """
        Cria ou atualiza lembretes para um agendamento.
        """
        # Remove lembretes existentes
        AppointmentReminder.objects.filter(appointment=appointment).delete()
        
        # Cria novos lembretes
        reminders = [
            {
                'type': '2_days',
                'delta': timedelta(days=2)
            },
            {
                'type': '1_day',
                'delta': timedelta(days=1)
            },
            {
                'type': 'same_day',
                'delta': timedelta(hours=3)
            }
        ]
        
        for reminder in reminders:
            AppointmentReminder.objects.create(
                appointment=appointment,
                reminder_type=reminder['type'],
                scheduled_for=appointment.date_time - reminder['delta']
            )

    def generate_reminder_message(self, reminder):
        """
        Gera uma mensagem de lembrete personalizada.
        """
        appointment = reminder.appointment
        reminder_type = reminder.get_reminder_type_display()
        
        return f"""Olá! Aqui é a {settings.AI_ASSISTANT_NAME}, sua assistente virtual.
        
        {reminder_type} da sua consulta agendada para {appointment.date_time.strftime('%d/%m/%Y às %H:%M')}.
        
        Por favor, confirme sua presença respondendo 'confirmo'.
        
        Se precisar remarcar, é só me avisar!
        
        Detalhes da consulta:
        {appointment.description}""" 