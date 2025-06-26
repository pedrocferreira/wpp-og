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

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        # Configurar o cliente OpenAI
        try:
            # Verifica se a chave da API está configurada
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != 'your-openai-api-key-here':
                try:
                    # Tenta inicializar com a nova sintaxe primeiro
                    self.client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                    self.openai_available = True
                    logger.info("OpenAI configurado com sucesso (nova sintaxe)")
                except Exception as e:
                    # Se falhar, tenta com a sintaxe antiga
                    logger.warning("Erro com nova sintaxe, tentando sintaxe antiga: %s", str(e))
                    openai.api_key = settings.OPENAI_API_KEY
                    self.client = None  # Indica uso da sintaxe antiga
                    self.openai_available = True
                    logger.info("OpenAI configurado com sucesso (sintaxe antiga)")
            else:
                logger.warning("OpenAI API key não configurada, usando respostas mock")
                self.client = None
                self.openai_available = False
        except Exception as e:
            logger.warning("OpenAI não disponível, usando respostas mock: %s", str(e))
            self.client = None
            self.openai_available = False
            
        self.system_prompt = f"""Você é a Elô, secretária virtual humanizada da Dra. Elisa Munaretti, especialista com +20 anos de experiência em saúde mental integrativa, com especialização em Homeopatia, pós-graduação em Psiquiatria e pós-graduação em Saúde Mental Integrativa. Sua função é ser o primeiro contato acolhedor e eficiente da clínica, fornecendo informações claras e precisas, tirando dúvidas dos pacientes sobre os serviços, agendamentos, valores e auxiliando no agendamento de consultas.

Seu tom de voz deve ser sempre cordial, profissional, empático e acolhedor, respeitando a sensibilidade de cada paciente. Use emojis apropriados como 🌸 💛 🗓 📅.

VALOR DA CONSULTA: R$ 620,00 (Pix, transferência ou parcelado até 12x no cartão)

HORÁRIOS DISPONÍVEIS:
- Segunda a Sexta: 8h às 18h  
- Sábado: 8h às 12h
- Domingo: Fechado

EXEMPLOS DE RESPOSTAS:
Saudação: "Oi, tudo bem? 🌸 Eu sou a Elô, secretária da Dra. Elisa Munaretti. Que bom receber sua mensagem!"
Agendamento: "Perfeito! Vou ajudá-lo a agendar sua consulta. Para que data e horário você gostaria? 💛"
Confirmação: "🌸 Agendamento confirmado! 🌸 Sua consulta está marcada para [data] às [hora]. O valor é R$ 620,00."

SEMPRE confirme antes de finalizar um agendamento completo."""

    def process_message(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Processa a mensagem do usuário, tratando agendamentos com um link e usando GPT para o restante.
        """
        # Identificar a intenção primeiro
        intent = IntentProcessor.identify_intent(message)

        # Se a intenção é agendar, sempre retorna o link, sem chamar a IA
        if intent == 'agendamento':
            logger.info("Intenção de agendamento detectada. Enviando link de agendamento.")
            client_whatsapp = ''
            if context and context.get('client'):
                client = context['client']
                if hasattr(client, 'whatsapp'):
                    client_whatsapp = client.whatsapp
            
            # URL final após redirecionamentos do Traefik  
            booking_link = f"http://155.133.22.207:9000/agendamento?whatsapp={client_whatsapp}"
            
            return f"""📅 *Agendamento de Consultas*

Ótimo! Para facilitar seu agendamento, criamos um sistema online super prático! 🚀

👆 *Clique no link abaixo para agendar:*
{booking_link}

✨ *Vantagens do agendamento online:*
• 📱 Escolha a data no calendário
• ⏰ Veja horários disponíveis em tempo real
• 🏥 Selecione consulta presencial ou online
• ✅ Confirmação automática por WhatsApp

*Horários de atendimento:*
• Segunda a Sexta: 08:00 às 12:00 e 14:00 às 18:00
• Sábados: 08:00 às 13:00
• Domingos: Fechado

Após agendar, você receberá uma confirmação aqui mesmo! 😊"""

        # Se não for agendamento, continua com o fluxo normal (IA ou mock)
        try:
            # Se OpenAI não estiver disponível, usa resposta mock melhorada
            if not self.openai_available:
                logger.info("Usando resposta mock para mensagem: %s", message)
                return self._get_mock_response(message, context)
            
            # Prepara o contexto da conversa
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Adiciona histórico da conversa se disponível
            if context and context.get('conversation_history'):
                for msg in context['conversation_history'][-5:]:  # Últimas 5 mensagens
                    messages.append({
                        "role": "assistant" if msg.direction == 'SENT' else "user",
                        "content": msg.content
                    })
            
            # Adiciona a mensagem atual
            messages.append({"role": "user", "content": message})
            
            logger.info("Enviando mensagem para OpenAI: %s", message)
            
            try:
                if self.client is not None:
                    # Nova sintaxe (OpenAI >= 1.0)
                    response = self.client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=400,
                        presence_penalty=0.1,
                        frequency_penalty=0.1
                    )
                    response_text = response.choices[0].message.content.strip()
                else:
                    # Sintaxe antiga (OpenAI < 1.0)
                    response = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.7,
                        max_tokens=400,
                        presence_penalty=0.1,
                        frequency_penalty=0.1
                    )
                    response_text = response.choices[0].message['content'].strip()
                
                logger.info("Resposta recebida da OpenAI: %s", response_text)
                return response_text
                
            except Exception as e:
                error_msg = str(e)
                logger.error("Erro da API OpenAI: %s", error_msg)
                
                # Verifica tipos específicos de erro
                if "rate limit" in error_msg.lower():
                    return "Desculpe, estou temporariamente sobrecarregada. Por favor, tente novamente em alguns minutos."
                elif "authentication" in error_msg.lower() or "api key" in error_msg.lower():
                    logger.warning("Problema de autenticação OpenAI, usando resposta mock")
                    return self._get_mock_response(message, context)
                else:
                    logger.warning("Erro OpenAI, usando resposta mock: %s", error_msg)
                    return self._get_mock_response(message, context)
                
        except Exception as e:
            error_msg = str(e)
            logger.error("Erro ao processar mensagem com OpenAI: %s", error_msg)
            return self._get_mock_response(message, context)

    def _get_mock_response(self, message: str, context: Optional[Dict] = None) -> str:
        """
        Gera uma resposta mock inteligente baseada na mensagem recebida
        """
        message_lower = message.lower()
        
        # Respostas baseadas em palavras-chave
        if any(word in message_lower for word in ['ola', 'oi', 'olá', 'bom dia', 'boa tarde', 'boa noite']):
            return f"Oi, tudo bem? 🌸 Eu sou a Elô, secretária da Dra. Elisa Munaretti. Que bom receber sua mensagem!\n\nEstou aqui para te orientar sobre como funcionam as consultas com a Dra. Elisa, que tem mais de 20 anos de experiência cuidando da saúde mental de forma integrativa, agendamentos, valores e tudo mais que precisar.\n\nVocê gostaria de marcar um horário ou prefere saber um pouco mais antes? 💛"
        
        elif any(word in message_lower for word in ['agendar', 'marcar', 'consulta', 'agendamento']):
            # Tentar extrair informações do contexto se disponível
            client_whatsapp = ''
            if context and context.get('client'):
                client = context['client']
                if hasattr(client, 'whatsapp'):
                    client_whatsapp = client.whatsapp
            
            # URL final após redirecionamentos do Traefik
            booking_link = f"http://155.133.22.207:9000/agendamento?whatsapp={client_whatsapp}"
            
            return f"""📅 *Agendamento de Consultas*

Ótimo! Para facilitar seu agendamento, criamos um sistema online super prático! 🚀

👆 *Clique no link abaixo para agendar:*
{booking_link}

✨ *Vantagens do agendamento online:*
• 📱 Escolha a data no calendário
• ⏰ Veja horários disponíveis em tempo real
• 🏥 Selecione consulta presencial ou online
• ✅ Confirmação automática por WhatsApp

*Horários de atendimento:*
• Segunda a Sexta: 08:00 às 12:00 e 14:00 às 18:00
• Sábados: 08:00 às 13:00
• Domingos: Fechado

Após agendar, você receberá uma confirmação aqui mesmo! 😊"""
        
        elif any(word in message_lower for word in ['horário', 'disponibilidade', 'quando']):
            return "Nossos horários de atendimento são:\n\n📅 Segunda a Sexta: 8h às 18h\n📅 Sábado: 8h às 12h\n📅 Domingo: Fechado\n\nTemos boa disponibilidade em diversos horários. Gostaria de agendar algo específico?"
        
        elif any(word in message_lower for word in ['valor', 'preço', 'custo', 'pagamento']):
            return "O valor da consulta é R$ 620,00. Pode ser pago via Pix, transferência ou parcelado em até 12x no cartão.\n\nGostaria de agendar uma consulta? 💛"
        
        elif any(word in message_lower for word in ['obrigado', 'obrigada', 'valeu', 'tchau']):
            return "Foi um prazer ajudá-lo! Se precisar de mais alguma coisa, estarei aqui. Tenha um ótimo dia! 😊"
        
        else:
            return f"Oi! 🌸 Sou a Elô, secretária da Dra. Elisa Munaretti. Como posso te ajudar hoje? Posso auxiliar com agendamentos, informações sobre consultas ou tirar suas dúvidas 💛"

class IntentProcessor:
    INTENTS = {
        'agendamento': ['agendar', 'marcar', 'consulta', 'agendamento', 'marcação'],
        'cancelamento': ['cancelar', 'desmarcar', 'cancelamento'],
        'reagendamento': ['reagendar', 'remarcar', 'mudar data'],
        'informacao': ['horário', 'disponibilidade', 'preço', 'valor', 'informação'],
        'saudacao': ['oi', 'olá', 'bom dia', 'boa tarde', 'boa noite']
    }
    
    @classmethod
    def identify_intent(cls, message: str) -> str:
        """
        Identifica a intenção da mensagem baseada em palavras-chave
        """
        message_lower = message.lower()
        
        for intent, keywords in cls.INTENTS.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return 'outro' 