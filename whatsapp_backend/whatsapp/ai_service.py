import openai
from django.conf import settings
import logging
from datetime import datetime, timedelta
import json
from appointments.models import Appointment, AppointmentReminder
from django.utils import timezone
import pytz
from typing import Dict, Optional
from .models import Message
from authentication.models import Client
from .models import WhatsAppMessage
from .evolution_service import EvolutionService

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Configurar o cliente OpenAI para a versão 1.3.0
        try:
            self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
            self.openai_available = True
        except Exception as e:
            logger.warning("OpenAI não disponível, usando respostas mock: %s", str(e))
            self.client = None
            self.openai_available = False
            
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
        {{
            "intent": "schedule_appointment",
            "data": {{
                "date": "YYYY-MM-DD",
                "time": "HH:MM",
                "description": "Descrição da consulta",
                "action": "schedule|reschedule|cancel|confirm"
            }}
        }}
        
        Mantenha as respostas concisas e objetivas, sempre com um tom amigável e prestativo."""

    def process_message(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Processa a mensagem do usuário usando GPT para determinar a intenção e gerar resposta
        """
        try:
            # Se OpenAI não estiver disponível, usa resposta mock
            if not self.openai_available:
                logger.info("Usando resposta mock para mensagem: %s", message)
                return self._get_mock_response(message)
            
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": message}
            ]
            
            if context and context.get('conversation_history'):
                for msg in context['conversation_history']:
                    messages.append({
                        "role": "assistant" if msg.is_from_bot else "user",
                        "content": msg.content
                    })
            
            logger.info("Enviando mensagem para OpenAI: %s", json.dumps(messages))
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=300
                )
                
                response_text = response.choices[0].message.content
                logger.info("Resposta recebida da OpenAI: %s", response_text)
                
                # Tenta processar a resposta como JSON se for um agendamento
                try:
                    response_data = json.loads(response_text)
                    if response_data.get('intent') == 'schedule_appointment':
                        self._process_appointment(response_data['data'], context)
                except json.JSONDecodeError:
                    # Se não for JSON, é uma resposta normal
                    pass
                    
                return response_text
                
            except Exception as e:
                error_msg = str(e)
                logger.error("Erro da API OpenAI: %s", error_msg)
                
                # Verifica tipos específicos de erro baseado na mensagem
                if "rate limit" in error_msg.lower():
                    return "Desculpe, estou temporariamente sobrecarregada. Por favor, tente novamente em alguns minutos."
                elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                    return "Desculpe, estou tendo problemas técnicos. Por favor, entre em contato com o suporte."
                else:
                    return "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
                
        except Exception as e:
            error_msg = str(e)
            logger.error("Erro ao processar mensagem com OpenAI: %s", error_msg)
            return "Desculpe, estou tendo problemas para processar sua mensagem. Por favor, tente novamente em alguns instantes."

    def _get_mock_response(self, message: str) -> str:
        """
        Gera uma resposta mock baseada na mensagem recebida
        """
        message_lower = message.lower()
        
        # Respostas baseadas em palavras-chave
        if any(word in message_lower for word in ['ola', 'oi', 'olá', 'bom dia', 'boa tarde', 'boa noite']):
            return f"Olá! Eu sou a {settings.AI_ASSISTANT_NAME}, sua assistente virtual. Como posso ajudá-lo hoje? Posso ajudar com agendamentos, informações sobre consultas ou tirar suas dúvidas."
        
        elif any(word in message_lower for word in ['agendar', 'marcar', 'consulta', 'agendamento']):
            return "Claro! Vou ajudá-lo a agendar uma consulta. Para isso, preciso de algumas informações: Em que data você gostaria de agendar? E qual horário seria melhor para você?"
        
        elif any(word in message_lower for word in ['cancelar', 'desmarcar', 'reagendar']):
            return "Entendi que você precisa cancelar ou reagendar uma consulta. Posso ajudá-lo com isso. Você poderia me informar qual consulta gostaria de alterar?"
        
        elif any(word in message_lower for word in ['horário', 'horarios', 'disponível', 'disponibilidade']):
            return "Nossos horários de atendimento são de segunda a sexta, das 8h às 18h. Temos disponibilidade para consultas em diversos horários. Gostaria de agendar algo específico?"
        
        elif any(word in message_lower for word in ['preço', 'valor', 'custo', 'quanto custa']):
            return "Para informações sobre valores e formas de pagamento, recomendo que entre em contato diretamente conosco. Posso ajudá-lo a agendar uma consulta onde poderemos esclarecer todas as questões financeiras."
        
        elif any(word in message_lower for word in ['obrigado', 'obrigada', 'valeu', 'tchau', 'até logo']):
            return "Foi um prazer ajudá-lo! Se precisar de mais alguma coisa, estarei aqui. Tenha um ótimo dia!"
        
        else:
            return f"Obrigada por entrar em contato! Sou a {settings.AI_ASSISTANT_NAME} e estou aqui para ajudá-lo. Posso auxiliar com agendamentos, informações sobre consultas e esclarecer suas dúvidas. Como posso ajudá-lo?"

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
            logger.error("Erro ao processar agendamento: %s", str(e))
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

    def process_agendamento(self, message: str, client: Client) -> str:
        """
        Processa uma mensagem de agendamento e retorna uma resposta apropriada
        """
        try:
            # Implementar lógica de processamento de agendamento
            pass
        except Exception as e:
            logger.error("Erro ao processar agendamento: %s", str(e))
            return "Desculpe, ocorreu um erro ao processar seu agendamento."

class IntentProcessor:
    INTENTS = {
        'agendamento': ['agendar', 'marcar', 'consulta', 'horário'],
        'informacao': ['informação', 'dúvida', 'horário', 'preço'],
        'cancelamento': ['cancelar', 'desmarcar', 'reagendar']
    }
    
    @classmethod
    def identify_intent(cls, message: str) -> str:
        message = message.lower()
        for intent, keywords in cls.INTENTS.items():
            if any(keyword in message for keyword in keywords):
                return intent
        return 'outros' 