import openai  # Ativado
from django.conf import settings
import logging
from datetime import datetime, timedelta
import json
from appointments.models import Appointment, Client
from django.utils import timezone
import pytz
from typing import Dict, Optional, Tuple
from .models import Message, WhatsAppMessage
from authentication.models import Client as AuthClient
from .natural_language_processor import NaturalLanguageProcessor
from .calendar_service import GoogleCalendarService
import re
import time
import threading

logger = logging.getLogger(__name__)

class SmartAIService:
    # Contexto compartilhado entre instâncias para persistir conversas
    _shared_conversation_context = {}
    
    def __init__(self):
        self.openai_client = None
        self.calendar_service = GoogleCalendarService()
        self.natural_language_processor = NaturalLanguageProcessor()
        
        # Inicializa OpenAI
        self._initialize_openai()
        
        # Sistema de contexto conversacional compartilhado
        self.conversation_context = SmartAIService._shared_conversation_context
        
        # Prompt system humanizado para GPT
        self.system_prompt = """Você é a Elô, secretária virtual da Dra. Elisa Munaretti, especialista em Saúde Mental Integrativa com mais de 20 anos de experiência.

PERSONALIDADE DA ELÔ:
- Brasileira, calorosa e empática
- Fala de forma natural e informal (usa "tá", "né", "eita")
- Sempre atenciosa e humana nas respostas
- Nunca robótica, sempre contextual
- Usa emojis para tornar a conversa mais amigável

INFORMAÇÕES DA CLÍNICA:
- Primeira consulta: R$ 620,00
- Retorno: R$ 350,00
- Horários: Seg-Sex 8h-18h, Sáb 8h-13h
- Especialidades: Homeopatia, Psiquiatria, Saúde Mental Integrativa

FUNÇÕES PRINCIPAIS:
1. Agendar consultas de forma natural
2. Responder dúvidas sobre valores e horários
3. Manter conversas empáticas e acolhedoras
4. Verificar disponibilidade de agenda

ESTILO DE COMUNICAÇÃO:
- "Oi! Tudo bom?" (saudação)
- "Claro que sim!" (confirmações)
- "Deixa eu verificar..." (verificações)
- "Eita! Que pena..." (empatia)
- "Perfeito!" (entusiasmo)
- "Como posso te ajudar?" (oferta de ajuda)

INSTRUÇÕES IMPORTANTES:
- SEMPRE seja contextual à conversa anterior
- Se cliente já mencionou algo, referencie naturalmente
- Para agendamentos, seja específica sobre data/hora
- Se não tiver certeza, peça mais informações
- Mantenha tom acolhedor mesmo em situações difíceis"""
        
        logger.info("SmartAI Service inicializado com integração Google Calendar real")
        
        self.timezone = pytz.timezone('America/Sao_Paulo')
        
        self.system_prompt = """Você é a Elô, secretária virtual da Dra. Elisa Munaretti, especialista em saúde mental integrativa.

PERSONALIDADE E ESTILO:
- Seja humana, calorosa e conversacional como uma secretária real brasileira
- Use linguagem INFORMAL brasileira: "tá", "né", "opa", "eita", "ai que pena"
- Seja CONTEXTUAL - sempre considere mensagens anteriores da conversa
- Mantenha mensagens CURTAS e naturais (1-2 frases)
- Varie suas respostas para não repetir frases
- Use emojis naturalmente, mas com moderação

CAPACIDADES DE CONTEXTO:
- SEMPRE lembre de conversas anteriores
- Se cliente já perguntou algo, faça referência ("como você perguntou...")
- Se tem agendamento existente, mencione naturalmente
- Mantenha fluência e coerência conversacional
- Responda baseado no histórico da conversa

INFORMAÇÕES DO CONSULTÓRIO:
- Dra. Elisa Munaretti - Saúde Mental Integrativa
- Valores: Primeira consulta R$ 620,00 | Retorno R$ 350,00
- Horários: Segunda-Sexta 8h-12h e 14h-18h | Sábado 8h-13h

DETECÇÃO DE AGENDAMENTOS:
- Qualquer menção a dia + horário = intenção de agendamento
- "quero amanha as 18" = agendamento 
- "as 15h tem?" = consulta disponibilidade
- "quinta 14h" = agendamento
- SEMPRE oferece para verificar disponibilidade

FLUXO DE AGENDAMENTO:
1. Cliente menciona dia/hora → "Deixa eu verificar..."
2. Sistema verifica automaticamente
3. Confirma ou sugere alternativas

EXAMPLES DE CONTEXTO:
Cliente: "Oi"
Você: "Oi! Tudo bom? 😊"

Cliente: "Quero agendar"
Você: "Claro! Que dia e horário você prefere?"

Cliente: "Amanha as 18"
Você: "Perfeito! Deixa eu verificar se amanhã às 18h tá livre..."

PRINCÍPIO FUNDAMENTAL: Seja CONTEXTUAL e HUMANA. Cada resposta deve considerar toda a conversa anterior e fluir naturalmente como se fosse uma pessoa real conversando."""

    def process_message(self, message_text, client_whatsapp, client_name=None):
        """Processa uma mensagem usando GPT quando disponível"""
        try:
            logger.info(f"Processando mensagem: '{message_text}' do cliente {client_whatsapp}")
            
            # Atualiza contexto conversacional
            self._update_conversation_context(client_whatsapp, message_text, client_name)
            
            # Busca agendamentos existentes para verificações
            context = self.conversation_context.get(client_whatsapp, {})
            existing_appointments = context.get('current_appointments', [])
            
            # PRIORIDADE 1: Verifica se é pedido de cancelamento/desmarcação
            if self._is_cancellation_request(message_text):
                return self._handle_cancellation_request(message_text, client_whatsapp, existing_appointments)
            
            # PRIORIDADE 2: Verifica se é pergunta sobre consultas existentes
            if self._is_consultation_inquiry(message_text):
                return self._handle_consultation_inquiry(message_text, client_whatsapp, existing_appointments)
            
            # PRIORIDADE 3: Verifica se é pergunta sobre disponibilidade
            if self._is_availability_question(message_text):
                return self._handle_availability_question(message_text, client_whatsapp)
            
            # PRIORIDADE 4: Verifica se é agendamento específico
            has_appointment_intent = self.natural_language_processor.extract_appointment_intent(message_text)
            extracted_datetime = None
            
            if has_appointment_intent:
                extracted_datetime = self.natural_language_processor.extract_datetime(message_text)
                if extracted_datetime:
                    logger.info(f"Data/hora específica detectada: {extracted_datetime}")
                    return self._handle_specific_appointment(message_text, client_whatsapp, client_name, extracted_datetime)
            
            # Se não é agendamento específico, usa GPT ou fallback
            if self.openai_client and self.openai_available:
                response = self._generate_gpt_response(message_text, client_whatsapp, client_name, has_appointment_intent)
            else:
                # Fallback para respostas programadas
                response = self._generate_fallback_response(message_text, client_whatsapp, client_name, has_appointment_intent)
            
            # Adiciona resposta ao contexto para manter histórico
            if response:
                self._add_assistant_response_to_context(client_whatsapp, response)
            
            return response
                
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            return "Oi! Tudo bem? Como posso te ajudar hoje? 😊"
    
    def _handle_specific_appointment(self, message_text, client_whatsapp, client_name, extracted_datetime):
        """Processa agendamento com data/hora específicos - versão humanizada"""
        try:
            # Valida horário de funcionamento
            if not self._is_valid_business_hours(extracted_datetime):
                return self._invalid_business_hours_response()
            
            # Primeira mensagem imediata - confirma que vai verificar
            time_str = extracted_datetime.strftime('%H:%M')
            if extracted_datetime.date() == datetime.now().date():
                day_ref = "hoje"
            elif extracted_datetime.date() == datetime.now().date() + timedelta(days=1):
                day_ref = "amanhã"
            else:
                weekdays = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
                weekday = weekdays[extracted_datetime.weekday()]
                day_ref = f"na {weekday}"
            
            checking_message = f"Perfeito! Deixa eu verificar se {day_ref} às {time_str} está livre... ⏳"
            
            # Envia mensagem de verificação e programa resposta
            self._send_checking_and_result(client_whatsapp, checking_message, extracted_datetime, client_name)
            
            # Retorna None para não enviar resposta imediata
            return None
                
        except Exception as e:
            logger.error(f"Erro ao processar agendamento específico: {e}")
            return "Ai, desculpa! Deu uma complicação aqui... Pode repetir o dia e horário que você quer agendar?"
    
    def _send_checking_and_result(self, client_whatsapp, checking_message, extracted_datetime, client_name):
        """Envia mensagem de verificação e depois o resultado com delay"""
        def process_appointment():
            try:
                # Envia primeira mensagem imediatamente
                from .evolution_service import EvolutionService
                evolution_service = EvolutionService()
                evolution_service.send_message(client_whatsapp, checking_message)
                
                # Aguarda alguns segundos para simular verificação
                time.sleep(3)
                
                # Verifica disponibilidade
                is_available = self._check_availability(extracted_datetime)
                
                if is_available:
                    # Cria o agendamento
                    appointment = self._create_appointment(
                        client_whatsapp, 
                        extracted_datetime, 
                        client_name
                    )
                    
                    if appointment:
                        # Mensagem de confirmação humanizada
                        confirmation = self._generate_humanized_confirmation(
                            client_name or "Cliente", 
                            extracted_datetime
                        )
                        evolution_service.send_message(client_whatsapp, confirmation)
                    else:
                        evolution_service.send_message(
                            client_whatsapp, 
                            "Ops, deu uma travada aqui no sistema... 😅\n\nPode me falar de novo o dia e horário? Já já consigo resolver!"
                        )
                else:
                    # Sugere horários alternativos de forma humanizada
                    alternative_slots = self._get_alternative_slots(extracted_datetime)
                    alternatives = self._suggest_alternatives_human_v2(extracted_datetime, alternative_slots)
                    evolution_service.send_message(client_whatsapp, alternatives)
                    
            except Exception as e:
                logger.error(f"Erro no processamento delayed: {e}")
                evolution_service.send_message(
                    client_whatsapp, 
                    "Ai, deu um probleminha aqui... 😅 Pode tentar de novo?"
                )
        
        # Executa em thread separada
        threading.Thread(target=process_appointment, daemon=True).start()
    
    def _generate_gpt_response(self, message_text, client_whatsapp, client_name, has_appointment_intent):
        """Gera resposta usando GPT com contexto conversacional"""
        try:
            # Busca contexto conversacional
            conversation_context = self._get_conversation_context_for_gpt(client_whatsapp)
            
            # Contexto adicional baseado na análise
            context = conversation_context
            if has_appointment_intent:
                context += "\n\nNOTA: O cliente mencionou agendamento. Seja específico sobre data/hora ou ofereça opções concretas."
            
            if client_name:
                context += f"\n\nO nome do cliente é {client_name}."
            
            # Prepara mensagens incluindo histórico completo
            system_content = f"""{self.system_prompt}

CONTEXTO CONVERSACIONAL:
{context}

INSTRUÇÕES PARA ESTA RESPOSTA:
- SEMPRE considere o histórico da conversa acima
- Se cliente já perguntou algo antes, referencie naturalmente
- Se tem agendamentos existentes, mencione de forma natural
- Se está perguntando disponibilidade específica, seja direto
- Mantenha fluidez conversacional como ChatGPT
- Seja contextual e humana, não robótica
"""
            
            # Inclui conversa real anterior no histórico do GPT
            context_obj = self.conversation_context.get(client_whatsapp, {})
            recent_messages = context_obj.get('messages', [])[-6:]  # Últimas 6 mensagens
            
            messages = [{"role": "system", "content": system_content}]
            
            # Inclui pares de pergunta-resposta REAIS da conversa anterior
            all_messages = context_obj.get('messages', [])[-10:]  # Últimas 10 mensagens
            
            # Processa mensagens em pares (user -> assistant)
            i = 0
            while i < len(all_messages) - 1:  # -1 para excluir mensagem atual
                current_msg = all_messages[i]
                
                if current_msg['type'] == 'user':
                    messages.append({"role": "user", "content": current_msg['content']})
                    
                    # Procura próxima mensagem de assistente
                    if i + 1 < len(all_messages) and all_messages[i + 1]['type'] == 'assistant':
                        assistant_msg = all_messages[i + 1]
                        messages.append({"role": "assistant", "content": assistant_msg['content']})
                        i += 2  # Pula as duas mensagens processadas
                    else:
                        # Se não há resposta do assistente, gera baseada no contexto
                        if current_msg.get('intent', {}).get('type') == 'availability':
                            messages.append({"role": "assistant", "content": "Deixa eu verificar a disponibilidade... 👀"})
                        elif current_msg.get('intent', {}).get('type') == 'greeting':
                            messages.append({"role": "assistant", "content": "Oi! Tudo bom? 😊"})
                        else:
                            messages.append({"role": "assistant", "content": "Entendi!"})
                        i += 1
                else:
                    i += 1
            
            # Mensagem atual
            messages.append({"role": "user", "content": message_text})
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=300,
                temperature=0.7
            )
            
            gpt_response = response.choices[0].message.content.strip()
            logger.info(f"[GPT] Resposta gerada: {gpt_response[:100]}...")
            
            # Salva a resposta no contexto para manter histórico real
            self._add_assistant_response_to_context(client_whatsapp, gpt_response)
            
            return gpt_response
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta GPT: {e}")
            return self._generate_fallback_response(message_text, client_whatsapp, client_name, has_appointment_intent)
    
    def _generate_fallback_response(self, message_text, client_whatsapp, client_name, has_appointment_intent):
        """Fallback inteligente para quando GPT não está disponível"""
        logger.info(f"[FALLBACK] Processando: '{message_text}', Intent: {has_appointment_intent}")
        
        # Busca contexto conversacional
        context = self.conversation_context.get(client_whatsapp, {})
        existing_appointments = context.get('current_appointments', [])
        message_lower = message_text.lower()
        
        # Se tem intenção de agendamento, verifica se tem data/hora específica
        if has_appointment_intent:
            extracted_datetime = self.natural_language_processor.extract_datetime(message_text)
            if extracted_datetime:
                logger.info(f"[FALLBACK] Data/hora específica detectada: {extracted_datetime}")
                return self._handle_specific_appointment(message_text, client_whatsapp, client_name, extracted_datetime)
            elif self._is_availability_question(message_text):
                return self._handle_availability_question(message_text, client_whatsapp)
            else:
                return self._ask_for_clarification()
        
        # Verifica perguntas sobre disponibilidade mesmo sem intent de agendamento claro
        if self._is_availability_question(message_text):
            return self._handle_availability_question(message_text, client_whatsapp)
        
        # Verifica perguntas sobre consultas existentes
        if self._is_consultation_inquiry(message_text):
            return self._handle_consultation_inquiry(message_text, client_whatsapp, existing_appointments)
        
        # Verifica se é pedido de cancelamento/desmarcação
        if self._is_cancellation_request(message_text):
            return self._handle_cancellation_request(message_text, client_whatsapp, existing_appointments)
        
        # Saudações
        greetings = ['oi', 'olá', 'ola', 'bom dia', 'boa tarde', 'boa noite', 'e aí', 'eai']
        if any(greeting in message_lower for greeting in greetings):
            name_part = f", {client_name}" if client_name else ""
            base_greeting = f"Oi{name_part}! Tudo bom? 😊\n\n"
            
            # Menciona agendamentos existentes se houver
            if existing_appointments:
                if len(existing_appointments) == 1:
                    apt_date = existing_appointments[0].date_time.strftime('%d/%m às %H:%M')
                    base_greeting += f"Vi que você já tem consulta marcada para {apt_date}! 😊"
                else:
                    base_greeting += f"Vi que você já tem {len(existing_appointments)} consultas marcadas! 😊"
            else:
                base_greeting += f"Eu sou a Elô, trabalho com a Dra. Elisa!\n\n"
                base_greeting += f"Como posso te ajudar?"
            
            return base_greeting
        
        # Agradecimentos
        if any(word in message_lower for word in ['obrigado', 'obrigada', 'valeu', 'brigado', 'brigada']):
            return "De nada! 😊\n\nPrecisa de mais alguma coisa?"
        
        # Valores
        if any(word in message_lower for word in ['valor', 'preço', 'quanto custa', 'quanto é', 'precos']):
            return "Primeira consulta: R$ 620,00\nRetorno: R$ 350,00\n\nQuer agendar? 😊"
        
        # Despedidas
        if any(word in message_lower for word in ['tchau', 'até', 'falou']):
            return "Até mais! 😊"
        
        # Resposta padrão
        return "Como posso te ajudar? 😊"
    
    def _is_consultation_inquiry(self, message_text):
        """Detecta se a mensagem pergunta sobre consultas existentes"""
        message_lower = message_text.lower()
        
        inquiry_patterns = [
            'quando.*proxima.*consulta',
            'quando.*próxima.*consulta',
            'quando.*minha.*consulta',
            'qual.*minha.*consulta',
            'tenho.*consulta.*quando',
            'quando.*marcado',
            'quando.*agendado',
            'que dia.*consulta',
            'que horas.*consulta',
            'horario.*consulta',
            'horário.*consulta',
            'dia.*consulta',
            'consulta.*quando',
            'consulta.*que dia',
            'consulta.*que hora',
            'agenda.*quando',
            'agenda.*que dia',
            'marcada.*quando',
            'agendamento.*quando',
        ]
        
        return any(re.search(pattern, message_lower) for pattern in inquiry_patterns)
    
    def _is_cancellation_request(self, message_text):
        """Detecta se a mensagem é um pedido de cancelamento/desmarcação"""
        message_lower = message_text.lower()
        
        cancellation_patterns = [
            'desmarcar',
            'cancelar',
            'quero.*desmarcar',
            'quero.*cancelar',
            'preciso.*desmarcar',
            'preciso.*cancelar',
            'vou.*desmarcar',
            'vou.*cancelar',
            'tenho.*que.*desmarcar',
            'tenho.*que.*cancelar',
            'não.*posso.*ir',
            'nao.*posso.*ir',
            'não.*vou.*conseguir',
            'nao.*vou.*conseguir',
            'remarcar.*outro.*dia',
            'remarcar.*para.*outro',
            'mudar.*horario',
            'mudar.*horário',
            'trocar.*horario',
            'trocar.*horário',
        ]
        
        return any(re.search(pattern, message_lower) for pattern in cancellation_patterns)
    
    def _handle_cancellation_request(self, message_text, client_whatsapp, existing_appointments):
        """Trata pedidos de cancelamento de consultas"""
        if not existing_appointments:
            return "Não encontrei nenhuma consulta marcada para cancelar. 😊\n\nQuer agendar uma nova consulta?"
        
        if len(existing_appointments) == 1:
            apt = existing_appointments[0]
            
            # Cancela o agendamento
            try:
                # Cancela no Google Calendar se conectado
                google_cancelled = False
                if apt.google_calendar_event_id:
                    try:
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        admin_user = User.objects.get(is_superuser=True)
                        if self.calendar_service.load_credentials(admin_user):
                            google_cancelled = self.calendar_service.cancel_appointment(apt.google_calendar_event_id)
                            logger.info(f"Cancelamento Google Calendar: {'Sucesso' if google_cancelled else 'Erro'}")
                    except Exception as e:
                        logger.warning(f"Erro ao cancelar no Google Calendar: {e}")
                
                # Atualiza status no banco
                apt.status = 'cancelled'
                apt.save()
                
                apt_date = apt.date_time.strftime('%d/%m/%Y às %H:%M')
                
                logger.info(f"Consulta cancelada: {apt_date} para cliente {client_whatsapp}")
                
                return f"Pronto! Cancelei sua consulta do dia {apt_date}. ✅\n\nSe precisar agendar outro horário, é só me avisar! 😊"
                
            except Exception as e:
                logger.error(f"Erro ao cancelar consulta: {e}")
                return "Ops, aconteceu um erro ao cancelar sua consulta. 😅\n\nPode tentar novamente ou me avisar se precisar de ajuda!"
        
        else:
            # Múltiplas consultas - pede especificação
            response = "Você tem várias consultas marcadas:\n\n"
            for i, apt in enumerate(existing_appointments[:3], 1):
                apt_date = apt.date_time.strftime('%d/%m/%Y às %H:%M')
                response += f"{i}. {apt_date}\n"
            
            response += "\nQual você gostaria de cancelar? Me fala a data ou horário! 😊"
            return response
    
    def _handle_consultation_inquiry(self, message_text, client_whatsapp, existing_appointments):
        """Responde perguntas sobre consultas existentes"""
        if not existing_appointments:
            return "Opa! Você ainda não tem nenhuma consulta marcada.\n\nQuer agendar? Que dia e horário funcionam melhor pra você? 😊"
        
        if len(existing_appointments) == 1:
            apt = existing_appointments[0]
            apt_date = apt.date_time.strftime('%d/%m/%Y')
            apt_time = apt.date_time.strftime('%H:%M')
            
            # Calcula dias até a consulta
            today = datetime.now().date()
            apt_date_obj = apt.date_time.date()
            days_diff = (apt_date_obj - today).days
            
            if days_diff == 0:
                day_ref = "hoje"
            elif days_diff == 1:
                day_ref = "amanhã"
            elif days_diff <= 7:
                weekdays = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
                weekday = weekdays[apt.date_time.weekday()]
                day_ref = f"na {weekday}"
            else:
                day_ref = f"no dia {apt_date}"
            
            return f"Sua próxima consulta está marcada para {day_ref} às {apt_time}! 😊\n\nPrecisa de mais alguma coisa?"
        
        else:
            # Múltiplas consultas - mostra a próxima
            next_apt = existing_appointments[0]  # Já ordenado por data
            apt_date = next_apt.date_time.strftime('%d/%m/%Y às %H:%M')
            
            response = f"Sua próxima consulta é em {apt_date}! 😊\n\n"
            
            if len(existing_appointments) > 1:
                response += f"Você tem {len(existing_appointments)} consultas marcadas.\n\nQuer ver todas?"
            
            return response
    
    def _check_availability(self, requested_datetime):
        """Verifica se o horário está disponível"""
        try:
            end_datetime = requested_datetime + timedelta(hours=1)
            
            # Tenta verificar no Google Calendar primeiro
            google_available = True
            try:
                from django.contrib.auth import get_user_model
                User = get_user_model()
                admin_user = User.objects.get(is_superuser=True)
                if self.calendar_service.load_credentials(admin_user):
                    google_available = self.calendar_service.check_availability(
                        requested_datetime, 
                        end_datetime
                    )
                    logger.info(f"Verificação Google Calendar: {'Livre' if google_available else 'Ocupado'}")
            except Exception as e:
                logger.warning(f"Erro ao verificar Google Calendar: {e}")
                google_available = True  # Fallback
            
            # Verifica banco local
            existing_appointment = Appointment.objects.filter(
                date_time=requested_datetime,
                status__in=['scheduled', 'confirmed']
            ).exists()
            
            # Disponível apenas se ambos estiverem livres
            available = google_available and not existing_appointment
            logger.info(f"Disponibilidade final para {requested_datetime}: {'Livre' if available else 'Ocupado'}")
            
            return available
            
        except Exception as e:
            logger.error(f"Erro ao verificar disponibilidade: {e}")
            return False
    
    def _create_appointment(self, client_whatsapp, datetime_obj, client_name=None):
        """Cria um novo agendamento"""
        try:
            # Busca ou cria o cliente
            client, created = Client.objects.get_or_create(
                whatsapp=client_whatsapp,
                defaults={'name': client_name or 'Cliente'}
            )
            
            # Tenta carregar credenciais Google Calendar do usuário admin
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                admin_user = User.objects.get(is_superuser=True)
                calendar_connected = self.calendar_service.load_credentials(admin_user)
            except User.DoesNotExist:
                calendar_connected = False
                logger.warning("Usuário admin não encontrado para Google Calendar")
            
            google_event = None
            if calendar_connected:
                # Cria evento no Google Calendar
                google_event = self.calendar_service.create_appointment(
                    client.name,
                    client_whatsapp,
                    datetime_obj,
                    datetime_obj + timedelta(hours=1),
                    "Consulta agendada via WhatsApp"
                )
                logger.info(f"Evento criado no Google Calendar: {google_event.get('id') if google_event else 'Erro'}")
            else:
                logger.warning("Google Calendar não conectado - agendamento apenas no banco local")
            
            # Cria no banco local
            appointment = Appointment.objects.create(
                client=client,
                date_time=datetime_obj,
                google_calendar_event_id=google_event.get('id') if google_event else None,
                status='scheduled',
                source='whatsapp',
                description=f'Agendado via WhatsApp - {client_whatsapp}',
            )
            
            logger.info(f"Agendamento criado: {appointment.id}")
            return appointment
            
        except Exception as e:
            logger.error(f"Erro ao criar agendamento: {e}")
            return None
    
    def _is_valid_business_hours(self, datetime_obj):
        """Valida se está dentro do horário de funcionamento"""
        weekday = datetime_obj.weekday()
        hour = datetime_obj.hour
        
        # Domingo fechado
        if weekday == 6:
            return False
        
        # Sábado: 8h às 13h
        if weekday == 5:
            return 8 <= hour < 13
        
        # Segunda a sexta: 8h às 12h e 14h às 18h
        return (8 <= hour < 12) or (14 <= hour < 18)
    
    def _get_alternative_slots(self, requested_datetime):
        """Busca horários alternativos na mesma data"""
        date = requested_datetime.date()
        
        try:
            # Tenta buscar do Google Calendar
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_user = User.objects.get(is_superuser=True)
            if self.calendar_service.load_credentials(admin_user):
                available_slots = self.calendar_service.get_available_slots(date)
                if available_slots:
                    logger.info(f"Slots do Google Calendar: {available_slots}")
                    return available_slots[:3]
        except Exception as e:
            logger.warning(f"Erro ao buscar slots do Google Calendar: {e}")
        
        # Fallback para horários padrão
        return ['14:00', '15:00', '16:00']
    
    def _suggest_alternatives_human(self, requested_datetime, available_slots):
        """Sugere horários alternativos de forma mais humana"""
        date_str = requested_datetime.strftime('%d/%m')
        time_str = requested_datetime.strftime('%H:%M')
        
        # Determina o dia da semana em português
        weekdays = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
        weekday = weekdays[requested_datetime.weekday()]
        
        if requested_datetime.date() == datetime.now().date():
            day_ref = "hoje"
        elif requested_datetime.date() == datetime.now().date() + timedelta(days=1):
            day_ref = "amanhã"
        else:
            day_ref = f"na {weekday} ({date_str})"
        
        message = f"Ai, que pena! O horário das {time_str} {day_ref} já está ocupado..."
        
        if available_slots:
            message += f"\n\nMas olha só, tenho esses horários livres {day_ref}:"
            for slot in available_slots:
                hour_num = int(slot.split(':')[0])
                if hour_num < 12:
                    period = "da manhã"
                elif hour_num < 18:
                    period = "da tarde"
                else:
                    period = "da noite"
                message += f"\n• {slot} {period}"
            
            message += "\n\nQual desses funciona melhor pra você?"
        else:
            message += "\n\nE infelizmente não tenho mais nenhum horário livre nesse dia... Quer que eu veja outros dias pra você?"
        
        return message
    
    def _ask_for_clarification(self):
        """Pede mais informações sobre o agendamento de forma humana"""
        return "Que legal! 😊\n\nQue dia e horário você quer vir?"

    def _invalid_business_hours_response(self):
        """Resposta para horários fora do funcionamento de forma humana"""
        return "Opa! Esse horário a gente não atende... 😅\n\nNossos horários são:\nSegunda a sexta: 8h-12h e 14h-18h\nSábado: 8h-13h\n\nPode escolher outro horário?"

    def _initialize_openai(self):
        """Inicializa OpenAI"""
        self.openai_available = False
        self.openai_client = None
        try:
            if hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != 'your-openai-api-key-here':
                import openai
                
                # Inicialização simples e limpa
                self.openai_client = openai.OpenAI(
                    api_key=settings.OPENAI_API_KEY
                )
                
                self.openai_available = True
                logger.info("OpenAI inicializado com sucesso!")
            else:
                self.openai_available = False
                logger.warning("OpenAI API key não configurada - usando fallback inteligente")
        except Exception as e:
            logger.warning(f"OpenAI não disponível ({e}) - usando fallback inteligente")
            self.openai_available = False
            
        logger.info(f"OpenAI inicializado - Disponível: {self.openai_available}")
        
    def _send_delayed_message(self, client_whatsapp, message, delay_seconds=3):
        """Envia mensagem com delay para simular digitação humana"""
        def send_after_delay():
            time.sleep(delay_seconds)
            try:
                # Importa o serviço de evolução aqui para evitar imports circulares
                from .evolution_service import EvolutionService
                evolution_service = EvolutionService()
                result = evolution_service.send_message(client_whatsapp, message)
                
                # Salva no banco
                try:
                    from authentication.models import Client as AuthClient
                    auth_client = AuthClient.objects.filter(whatsapp=client_whatsapp).first()
                    if auth_client:
                        WhatsAppMessage.objects.create(
                            client=auth_client,
                            content=message,
                            message_type='SENT',
                            direction='SENT',
                            message_id=result.get('id', '') if result else ''
                        )
                except Exception as e:
                    logger.warning(f"Erro ao salvar mensagem delayed: {e}")
                    
                logger.info(f"[DELAYED] Mensagem enviada após {delay_seconds}s: {message[:50]}...")
            except Exception as e:
                logger.error(f"Erro ao enviar mensagem delayed: {e}")
        
        # Executa em thread separada
        threading.Thread(target=send_after_delay, daemon=True).start()
        
    def _split_long_message(self, message, max_length=150):
        """Divide mensagens longas em partes menores"""
        if len(message) <= max_length:
            return [message]
        
        parts = []
        current_part = ""
        
        # Divide por frases (pontos, exclamações, interrogações)
        sentences = re.split(r'([.!?]\s*)', message)
        
        for i in range(0, len(sentences), 2):
            sentence = sentences[i] if i < len(sentences) else ""
            punct = sentences[i+1] if i+1 < len(sentences) else ""
            full_sentence = sentence + punct
            
            if len(current_part + full_sentence) <= max_length:
                current_part += full_sentence
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = full_sentence
        
        if current_part:
            parts.append(current_part.strip())
        
        # Se ainda tem partes muito longas, divide por linha
        final_parts = []
        for part in parts:
            if len(part) <= max_length:
                final_parts.append(part)
            else:
                lines = part.split('\n')
                current_line_group = ""
                for line in lines:
                    if len(current_line_group + line + '\n') <= max_length:
                        current_line_group += line + '\n'
                    else:
                        if current_line_group:
                            final_parts.append(current_line_group.strip())
                        current_line_group = line + '\n'
                if current_line_group:
                    final_parts.append(current_line_group.strip())
        
        return final_parts if final_parts else [message]
    
    def _send_typing_indicator(self, client_whatsapp):
        """Simula indicador de digitação"""
        try:
            from .evolution_service import EvolutionService
            evolution_service = EvolutionService()
            # Aqui você pode implementar o indicador de digitação se a API suportar
            logger.info(f"[TYPING] Simulando digitação para {client_whatsapp}")
        except Exception as e:
            logger.warning(f"Erro ao enviar indicador de digitação: {e}")
        
    def _update_conversation_context(self, client_whatsapp, message_text, client_name=None):
        """Atualiza o contexto conversacional do cliente"""
        if client_whatsapp not in self.conversation_context:
            self.conversation_context[client_whatsapp] = {
                'messages': [],
                'client_name': client_name,
                'last_appointment_search': None,
                'current_appointments': None,
                'conversation_state': 'initial',
                'pending_appointment': None,  # Para agendamentos em processo
                'last_availability_check': None,  # Última consulta de disponibilidade
                'conversation_summary': []  # Resumo das últimas interações importantes
            }
        
        context = self.conversation_context[client_whatsapp]
        
        # Detecta informações importantes da mensagem
        intent_info = self._extract_conversation_intent(message_text)
        
        # Adiciona mensagem ao histórico (aumentado para 20 mensagens)
        context['messages'].append({
            'timestamp': datetime.now(),
            'content': message_text,
            'type': 'user',
            'intent': intent_info,
            'date': datetime.now().date()  # Adiciona data para detectar mudanças de dia
        })
        
        # Mantém apenas últimas 20 mensagens
        if len(context['messages']) > 20:
            context['messages'] = context['messages'][-20:]
        
        # Atualiza resumo conversacional baseado na intent
        self._update_conversation_summary(context, message_text, intent_info)
        
        # Atualiza nome se fornecido
        if client_name:
            context['client_name'] = client_name
            
        # Verifica se cliente tem agendamentos existentes
        try:
            from appointments.models import Client, Appointment
            client = Client.objects.filter(whatsapp=client_whatsapp).first()
            if client:
                existing_appointments = Appointment.objects.filter(
                    client=client,
                    status__in=['scheduled', 'confirmed'],
                    date_time__gte=datetime.now()
                ).order_by('date_time')
                
                # Sincroniza status com Google Calendar
                existing_appointments = self._sync_appointments_with_google_calendar(existing_appointments)
                context['current_appointments'] = list(existing_appointments)
        except Exception as e:
            logger.warning(f"Erro ao buscar agendamentos existentes: {e}")
            
        logger.info(f"[CONTEXT] Cliente {client_whatsapp}: {len(context['messages'])} mensagens, {len(context.get('current_appointments', []))} agendamentos")
        
    def _extract_conversation_intent(self, message_text):
        """Extrai informações contextuais importantes da mensagem"""
        message_lower = message_text.lower()
        intent_info = {
            'type': 'general',
            'datetime_mentioned': None,
            'appointment_intent': False,
            'availability_question': False,
            'cancellation_request': False
        }
        
        # Detecta data/hora mencionada
        try:
            extracted_dt = self.natural_language_processor.extract_datetime(message_text)
            if extracted_dt:
                intent_info['datetime_mentioned'] = extracted_dt
        except:
            pass
            
        # Detecta diferentes tipos de intent
        intent_info['appointment_intent'] = self.natural_language_processor.extract_appointment_intent(message_text)
        intent_info['availability_question'] = self._is_availability_question(message_text)
        intent_info['cancellation_request'] = self._is_cancellation_request(message_text)
        
        # Define tipo principal
        if intent_info['cancellation_request']:
            intent_info['type'] = 'cancellation'
        elif intent_info['availability_question']:
            intent_info['type'] = 'availability'
        elif intent_info['appointment_intent']:
            intent_info['type'] = 'appointment'
        elif any(word in message_lower for word in ['oi', 'olá', 'bom dia', 'boa tarde']):
            intent_info['type'] = 'greeting'
        elif any(word in message_lower for word in ['obrigado', 'valeu', 'ok', 'pode agendar', 'quero agendar']):
            intent_info['type'] = 'confirmation'
            
        return intent_info
        
    def _update_conversation_summary(self, context, message_text, intent_info):
        """Atualiza resumo das interações importantes"""
        timestamp = datetime.now()
        
        # Atualiza informações específicas baseadas na intent
        if intent_info['type'] == 'availability':
            if intent_info['datetime_mentioned']:
                context['last_availability_check'] = {
                    'datetime': intent_info['datetime_mentioned'],
                    'timestamp': timestamp,
                    'message': message_text
                }
                # Adiciona ao resumo
                date_str = intent_info['datetime_mentioned'].strftime('%d/%m às %H:%M')
                context['conversation_summary'].append(f"Cliente perguntou disponibilidade para {date_str}")
                
        elif intent_info['type'] == 'confirmation':
            # Se o cliente confirmou algo após uma consulta de disponibilidade
            if context.get('last_availability_check'):
                last_check = context['last_availability_check']
                context['pending_appointment'] = {
                    'datetime': last_check['datetime'],
                    'timestamp': timestamp,
                    'status': 'awaiting_confirmation'
                }
                date_str = last_check['datetime'].strftime('%d/%m às %H:%M')
                context['conversation_summary'].append(f"Cliente confirmou agendamento para {date_str}")
                
        elif intent_info['type'] == 'appointment' and intent_info['datetime_mentioned']:
            # Agendamento direto com data/hora
            context['pending_appointment'] = {
                'datetime': intent_info['datetime_mentioned'],
                'timestamp': timestamp,
                'status': 'direct_request'
            }
            date_str = intent_info['datetime_mentioned'].strftime('%d/%m às %H:%M')
            context['conversation_summary'].append(f"Cliente solicitou agendamento para {date_str}")
            
        # Mantém apenas últimos 5 itens do resumo
        if len(context['conversation_summary']) > 5:
            context['conversation_summary'] = context['conversation_summary'][-5:]
            
    def _add_assistant_response_to_context(self, client_whatsapp, response_text):
        """Adiciona resposta do assistente ao contexto para manter histórico real"""
        if client_whatsapp not in self.conversation_context:
            return
            
        context = self.conversation_context[client_whatsapp]
        
        # Adiciona resposta do assistente
        context['messages'].append({
            'timestamp': datetime.now(),
            'content': response_text,
            'type': 'assistant',
            'date': datetime.now().date()  # Adiciona data para detectar mudanças de dia
        })
        
        # Mantém limite de 20 mensagens
        if len(context['messages']) > 20:
            context['messages'] = context['messages'][-20:]
        
    def _get_conversation_context_for_gpt(self, client_whatsapp):
        """Prepara contexto conversacional enriquecido para o GPT"""
        if client_whatsapp not in self.conversation_context:
            return ""
            
        context = self.conversation_context[client_whatsapp]
        context_text = ""
        
        # Informações do cliente
        if context.get('client_name'):
            context_text += f"Nome do cliente: {context['client_name']}\n\n"
            
        # ESTADO ATUAL DA CONVERSA (muito importante!)
        if context.get('conversation_summary'):
            context_text += "RESUMO IMPORTANTE DA CONVERSA:\n"
            for summary_item in context['conversation_summary']:
                context_text += f"• {summary_item}\n"
            context_text += "\n"
            
        # Última consulta de disponibilidade (contexto crítico!)
        if context.get('last_availability_check'):
            last_check = context['last_availability_check']
            date_str = last_check['datetime'].strftime('%d/%m às %H:%M')
            context_text += f"🎯 IMPORTANTE: Cliente perguntou se há horário para {date_str}\n"
            context_text += f"   Sistema já verificou e confirmou que está DISPONÍVEL\n\n"
            
        # Agendamento pendente
        if context.get('pending_appointment'):
            pending = context['pending_appointment']
            date_str = pending['datetime'].strftime('%d/%m às %H:%M')
            if pending['status'] == 'awaiting_confirmation':
                context_text += f"⏳ PENDENTE: Cliente pode estar confirmando agendamento para {date_str}\n\n"
                
        # Agendamentos existentes
        if context.get('current_appointments'):
            context_text += f"Agendamentos já confirmados:\n"
            for apt in context['current_appointments']:
                apt_date = apt.date_time.strftime('%d/%m/%Y às %H:%M')
                context_text += f"- {apt_date}\n"
            context_text += "\n"
            
        # Histórico da conversa com detecção de mudanças de dia (últimas 12 mensagens com contexto)
        recent_messages = context['messages'][-12:]
        if len(recent_messages) > 1:  # Se há histórico
            context_text += "HISTÓRICO DA CONVERSA (últimas mensagens):\n"
            current_date = None
            
            for msg in recent_messages[:-1]:  # Exclui a mensagem atual
                msg_date = msg.get('date')
                timestamp = msg['timestamp'].strftime('%H:%M') if hasattr(msg['timestamp'], 'strftime') else "agora"
                intent_type = msg.get('intent', {}).get('type', 'general')
                
                # Detecta mudança de dia
                if msg_date and msg_date != current_date:
                    if current_date is not None:  # Não é a primeira mensagem
                        context_text += "--- NOVA CONVERSA (outro dia) ---\n"
                    else:
                        date_str = msg_date.strftime('%d/%m') if msg_date else "hoje"
                        context_text += f"=== Conversa do dia {date_str} ===\n"
                    current_date = msg_date
                
                # Formata tipo de mensagem
                if msg['type'] == 'user':
                    context_text += f"Cliente ({timestamp}) [{intent_type}]: {msg['content']}\n"
                else:
                    context_text += f"Assistente ({timestamp}): {msg['content']}\n"
                    
            context_text += "\n🎯 IMPORTANTE: Seja TOTALMENTE coerente com esta conversa. Não ignore o contexto!\n"
            context_text += "Se há uma conversa de outro dia, considere que pode ser uma nova interação.\n"
            
        return context_text
        
    def _is_availability_question(self, message_text):
        """Detecta se a mensagem é uma pergunta sobre disponibilidade de horário"""
        message_lower = message_text.lower()
        
        # Padrões específicos para perguntas de disponibilidade
        availability_patterns = [
            r'as?\s+\d{1,2}.*(?:tem|livre|disponível|\?)',  # "as 10 tem?" "as 14 tá livre?"
            r'\d{1,2}.*(?:da\s+)?(?:manhã|tarde|noite).*(?:tem|\?)',  # "10 da manha tem?"
            r'tem.*as?\s+\d{1,2}',  # "tem as 10?"
            r'pode.*as?\s+\d{1,2}',  # "pode as 15?"
            r'funciona.*as?\s+\d{1,2}',  # "funciona as 14?"
            r'dá.*as?\s+\d{1,2}',  # "dá as 16?"
            r'serve.*as?\s+\d{1,2}',  # "serve as 09?"
            r'\d{1,2}h.*(?:tem|livre|pode|\?)',  # "15h tem?" "14h pode?"
            r'(?:às|as)\s+\d{1,2}.*\?',  # "às 10?" "as 15?"
            r'tá.*livre.*\d{1,2}',  # "tá livre as 14?"
            r'vago.*\d{1,2}',  # "vago as 15?"
        ]
        
        for pattern in availability_patterns:
            if re.search(pattern, message_lower):
                return True
        
        return False
    
    def _handle_availability_question(self, message_text, client_whatsapp):
        """Trata especificamente perguntas sobre disponibilidade - versão humanizada"""
        logger.info(f"[AVAILABILITY] Processando pergunta: '{message_text}'")
        
        # Tenta extrair horário da pergunta
        extracted_datetime = self.natural_language_processor.extract_datetime(message_text)
        
        if extracted_datetime:
            time_str = extracted_datetime.strftime('%H:%M')
            
            if extracted_datetime.date() == datetime.now().date():
                day_ref = "hoje"
            elif extracted_datetime.date() == datetime.now().date() + timedelta(days=1):
                day_ref = "amanhã"
            else:
                weekdays = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
                weekday = weekdays[extracted_datetime.weekday()]
                day_ref = f"na {weekday}"
            
            # Mensagem imediata de verificação
            checking_message = f"Deixa eu dar uma olhadinha... 👀"
            
            # Envia verificação e resultado com delay
            self._send_availability_check_and_result(client_whatsapp, checking_message, extracted_datetime, time_str, day_ref)
            
            # Retorna None para não enviar resposta imediata
            return None
        else:
            # Se não conseguiu extrair horário específico
            return "Não consegui entender bem o horário que você quer saber... Pode me falar de novo? Tipo 'as 14h tem?' ou 'amanhã às 10 da manhã tem vaga?'"
    
    def _send_availability_check_and_result(self, client_whatsapp, checking_message, extracted_datetime, time_str, day_ref):
        """Envia verificação de disponibilidade com delay humanizado"""
        def check_and_respond():
            try:
                from .evolution_service import EvolutionService
                evolution_service = EvolutionService()
                
                # Envia mensagem de verificação
                evolution_service.send_message(client_whatsapp, checking_message)
                
                # Aguarda para simular verificação
                time.sleep(2)
                
                # Verifica disponibilidade
                is_available = self._check_availability(extracted_datetime)
                
                if is_available:
                    response = f"Sim! 🎉\n\n"
                    response += f"O horário das {time_str} {day_ref} está livre!\n\n"
                    response += f"Quer que eu agende pra você? 😊"
                else:
                    # Busca horários alternativos
                    available_slots = self._get_alternative_slots(extracted_datetime)
                    response = f"Ai, que pena! 😔\n\n"
                    response += f"Das {time_str} {day_ref} já está ocupado..."
                    
                    if available_slots:
                        response += f"\n\nMas tenho esses livres {day_ref}:\n\n"
                        for i, slot in enumerate(available_slots[:3], 1):
                            hour_num = int(slot.split(':')[0])
                            if hour_num < 12:
                                period = "da manhã"
                            elif hour_num < 18:
                                period = "da tarde"
                            else:
                                period = "da noite"
                            response += f"{i}. {slot} {period}\n"
                        response += f"\nQual funciona melhor? 😊"
                    else:
                        response += f"\n\nE não tenho mais horários livres {day_ref}... 😕\n\n"
                        response += f"Quer que eu veja outros dias?"
                
                evolution_service.send_message(client_whatsapp, response)
                
            except Exception as e:
                logger.error(f"Erro na verificação de disponibilidade: {e}")
                evolution_service.send_message(
                    client_whatsapp, 
                    "Ops, deu um probleminha aqui... 😅 Pode tentar de novo?"
                )
        
        # Executa em thread separada
        threading.Thread(target=check_and_respond, daemon=True).start()
    
    def _generate_humanized_confirmation(self, client_name, datetime_obj):
        """Gera mensagem de confirmação mais humanizada e dividida"""
        date_str = datetime_obj.strftime('%d/%m')
        time_str = datetime_obj.strftime('%H:%M')
        weekday = datetime_obj.strftime('%A')
        
        weekday_pt = {
            'Monday': 'segunda-feira',
            'Tuesday': 'terça-feira', 
            'Wednesday': 'quarta-feira',
            'Thursday': 'quinta-feira',
            'Friday': 'sexta-feira',
            'Saturday': 'sábado',
            'Sunday': 'domingo'
        }
        
        weekday_name = weekday_pt.get(weekday, weekday)
        
        if datetime_obj.date() == datetime.now().date():
            day_ref = "hoje"
        elif datetime_obj.date() == datetime.now().date() + timedelta(days=1):
            day_ref = "amanhã"
        else:
            day_ref = f"{weekday_name} ({date_str})"
        
        confirmation = f"Oba! Consegui agendar! 🎉\n\n"
        confirmation += f"Sua consulta está marcada para {day_ref} às {time_str}.\n\n"
        confirmation += f"Já salvei na agenda da Dra. Elisa! 📅"
        
        return confirmation
    
    def _suggest_alternatives_human_v2(self, requested_datetime, available_slots):
        """Versão mais humanizada de sugestão de alternativas"""
        time_str = requested_datetime.strftime('%H:%M')
        
        if requested_datetime.date() == datetime.now().date():
            day_ref = "hoje"
        elif requested_datetime.date() == datetime.now().date() + timedelta(days=1):
            day_ref = "amanhã"
        else:
            weekdays = ['segunda', 'terça', 'quarta', 'quinta', 'sexta', 'sábado', 'domingo']
            weekday = weekdays[requested_datetime.weekday()]
            day_ref = f"na {weekday}"
        
        message = f"Ai, que pena! 😔\n\n"
        message += f"O horário das {time_str} {day_ref} já está ocupado..."
        
        if available_slots:
            message += f"\n\nMas olha, tenho esses horários livres {day_ref}:\n\n"
            for i, slot in enumerate(available_slots[:3], 1):
                hour_num = int(slot.split(':')[0])
                if hour_num < 12:
                    period = "da manhã"
                elif hour_num < 18:
                    period = "da tarde"
                else:
                    period = "da noite"
                message += f"{i}. {slot} {period}\n"
            
            message += f"\nQual desses funciona pra você? 😊"
        else:
            message += f"\n\nE infelizmente não tenho mais horários livres {day_ref}... 😕\n\n"
            message += f"Quer que eu veja outros dias pra você?"
        
        return message 
    
    def _sync_appointments_with_google_calendar(self, appointments):
        """Sincroniza status dos agendamentos com Google Calendar"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            admin_user = User.objects.get(is_superuser=True)
            
            # Se Google Calendar não estiver conectado, retorna sem alteração
            if not self.calendar_service.load_credentials(admin_user):
                return appointments
            
            valid_appointments = []
            
            for apt in appointments:
                # Se tem ID do Google Calendar, verifica status
                if apt.google_calendar_event_id:
                    try:
                        event = self.calendar_service.service.events().get(
                            calendarId='primary',
                            eventId=apt.google_calendar_event_id
                        ).execute()
                        
                        # Se evento foi cancelado no Google Calendar, cancela no banco também
                        if event.get('status') == 'cancelled':
                            logger.info(f"Sincronizando cancelamento: {apt.date_time} - {apt.client.name}")
                            apt.status = 'cancelled'
                            apt.save()
                            continue  # Não adiciona à lista de válidos
                            
                    except Exception as e:
                        # Se evento não existe no Google Calendar, marca como cancelado
                        if "not found" in str(e).lower() or "404" in str(e):
                            logger.info(f"Evento não encontrado no Google Calendar, cancelando: {apt.date_time}")
                            apt.status = 'cancelled'
                            apt.save()
                            continue
                        else:
                            logger.warning(f"Erro ao verificar evento no Google Calendar: {e}")
                
                # Adiciona apenas agendamentos válidos
                if apt.status in ['scheduled', 'confirmed']:
                    valid_appointments.append(apt)
            
            logger.info(f"Sincronização concluída: {len(valid_appointments)} agendamentos válidos")
            return valid_appointments
            
        except Exception as e:
            logger.error(f"Erro na sincronização com Google Calendar: {e}")
            return appointments  # Retorna lista original em caso de erro 