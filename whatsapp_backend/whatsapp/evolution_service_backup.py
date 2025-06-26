import requests
import json
import logging
from django.conf import settings
from .models import EvolutionConfig, WhatsAppMessage
from authentication.models import Client as AuthClient
from datetime import datetime, timedelta
import re
from appointments.models import Client as AppointmentClient, ConversationState, Appointment

logger = logging.getLogger(__name__)

class EvolutionService:
    def __init__(self):
        self.config = EvolutionConfig.objects.filter(is_active=True).first()
        if not self.config:
            raise ValueError("No active Evolution configuration found")
        
        self.base_url = settings.EVOLUTION_API_URL
        self.headers = {
            "Content-Type": "application/json",
            "apikey": self.config.api_key,
            "token": self.config.api_key
        }
        logger.info("Headers configurados: %s", json.dumps(self.headers))
        
        # Inicializa o serviço de IA inteligente
        from .smart_ai_service import SmartAIService
        self.ai_service = SmartAIService()

    def setup_webhook(self):
        """Configura o webhook no Evolution API"""
        url = f"{self.base_url}/instance/create"
        
        data = {
            "instanceName": self.config.instance_id,
            "token": self.config.api_key,
            "qrcode": True,
            "integration": "WHATSAPP",
            "webhook": {
                "url": self.config.webhook_url,
                "enabled": True
            },
            "events": [
                "messages.upsert",
                "messages.update",
                "qr.update",
                "connection.update",
                "contacts.upsert",
                "contacts.update"
            ]
        }
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

    def send_message(self, phone: str, message: str, media_url: str = None):
        """Envia uma mensagem via Evolution API"""
        try:
            # Remove o '@s.whatsapp.net' se existir no número
            phone = phone.replace('@s.whatsapp.net', '')
            
            url = f"{self.base_url}/message/sendText/{settings.EVOLUTION_INSTANCE_ID}"
            
            data = {
                "number": phone,
                "text": message,
                "linkPreview": True  # Habilita preview de links se houver
            }
            
            # Log usando formatação correta
            logger.info("Enviando mensagem para %s: %s", phone, message)
            logger.info("URL: %s", url)
            logger.info("Headers: %s", json.dumps(self.headers))
            logger.info("Data: %s", json.dumps(data))
            
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code != 200:
                logger.error("Resposta da API: %s", response.text)
            response.raise_for_status()
            
            result = response.json()
            logger.info("Mensagem enviada com sucesso para %s: %s", phone, json.dumps(result))
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error("Erro ao enviar mensagem: %s", str(e))
            raise

    def _get_or_create_client(self, phone: str, name: str = None) -> AuthClient:
        """
        Busca ou cria um cliente com base no número do WhatsApp
        """
        try:
            # Remove o '@s.whatsapp.net' se existir no número
            phone = phone.replace('@s.whatsapp.net', '')
            
            # Busca ou cria o cliente
            client, created = AuthClient.objects.get_or_create(
                whatsapp=phone,
                defaults={
                    'name': name or phone
                }
            )
            
            # Se o cliente já existia mas não tinha nome, atualiza
            if not created and name and not client.name:
                client.name = name
                client.save()
            
            return client
            
        except Exception as e:
            logger.error("Erro ao buscar/criar cliente: %s", str(e))
            raise

    def process_webhook(self, data: dict):
        """Processa o webhook recebido da Evolution API"""
        try:
            logger.info("Processando webhook: %s", json.dumps(data))
            
            # Extrai a chave de API do webhook
            webhook_api_key = data.get('apikey')
            if webhook_api_key:
                self.headers['apikey'] = webhook_api_key
                self.headers['token'] = webhook_api_key
                logger.info("Headers atualizados com a chave do webhook: %s", json.dumps(self.headers))
            
            if data.get('event') == 'messages.upsert':
                logger.info("Evento messages.upsert detectado")
                message_data = data.get('data', {})
                if not message_data:
                    logger.warning("Dados da mensagem não encontrados")
                    return
                
                # Extrai informações da mensagem
                key = message_data.get('key', {})
                message = message_data.get('message', {})
                message_type = message_data.get('messageType')  # Campo correto
                
                logger.info("Key extraída: %s", json.dumps(key))
                logger.info("Message extraída: %s", json.dumps(message))
                logger.info("MessageType: %s", message_type)
                
                # Verifica se é uma mensagem de texto
                if message_type == 'conversation':
                    logger.info("Mensagem de conversação detectada")
                    content = message.get('conversation', '')
                    if not content:
                        logger.warning("Conteúdo da mensagem não encontrado")
                        return
                    
                    logger.info("Conteúdo da mensagem: %s", content)
                    
                    # Extrai o número do telefone
                    remote_jid = key.get('remoteJid', '')
                    if not remote_jid:
                        logger.warning("Número do telefone não encontrado")
                        return
                    
                    # Remove o sufixo @s.whatsapp.net
                    phone = remote_jid.split('@')[0]
                    logger.info("Número do telefone extraído: %s", phone)
                    
                    # Buscar ou criar o cliente do authentication para WhatsAppMessage
                    auth_client, _ = AuthClient.objects.get_or_create(
                        whatsapp=phone,
                        defaults={'name': message_data.get('pushName', 'Cliente WhatsApp')}
                    )

                    # Buscar ou criar o cliente do appointments para agendamento
                    appointment_client, created = AppointmentClient.objects.get_or_create(
                        whatsapp=phone,
                        defaults={'name': message_data.get('pushName', 'Cliente WhatsApp')}
                    )
                    logger.info("Cliente %s: %s", "criado" if created else "encontrado", appointment_client.whatsapp)

                    # Buscar ou criar estado da conversa
                    conversation_state, _ = ConversationState.objects.get_or_create(client=appointment_client)

                    # Salva a mensagem no banco (WhatsAppMessage deve usar auth_client)
                    message_obj = WhatsAppMessage.objects.create(
                        client=auth_client,
                        content=content,
                        message_type='RECEIVED',
                        direction='RECEIVED',
                        message_id=key.get('id', '')
                    )
                    logger.info("Mensagem processada com sucesso: %s", json.dumps({
                        'id': message_obj.id,
                        'client': auth_client.whatsapp,
                        'content': message_obj.content
                    }))
                    
                    # Busca o histórico da conversa (últimas 10 mensagens)
                    conversation_history = WhatsAppMessage.objects.filter(
                        client=auth_client
                    ).order_by('-timestamp')[:10]
                    
                    # Prepara o contexto para o serviço de IA inteligente
                    context = {
                        'client': appointment_client,  # Cliente da tabela appointments
                        'auth_client': auth_client,    # Cliente da tabela authentication
                        'client_id': auth_client.id,
                        'conversation_history': list(reversed(conversation_history))  # Inverte para ordem cronológica
                    }
                    
                    # Usa o novo SmartAIService para processar a mensagem
                    logger.info("Processando mensagem com SmartAI: %s", content)
                    resposta = self.ai_service.process_message(content, context)
                    
                    # Envia a resposta e salva no banco
                    if resposta:
                        result = self.send_message(phone, resposta)
                        WhatsAppMessage.objects.create(
                            client=auth_client,
                            content=resposta,
                            message_type='SENT',
                            direction='SENT',
                            message_id=result.get('id', '') if result else ''
                        )
                        logger.info('Mensagem de resposta SmartAI enviada e salva no banco')
                        return  # Finaliza processamento com SmartAI

                    # Função auxiliar para detectar saudações
                    def eh_saudacao(texto):
                        saudacoes = ['olá', 'ola', 'oi', 'bom dia', 'boa tarde', 'boa noite', 'hello', 'hey']
                        return any(saudacao in texto.lower() for saudacao in saudacoes)

                    # RESETAR CONVERSA SE DETECTAR NOVA SAUDAÇÃO OU AGENDAMENTO
                    if eh_saudacao(content) and conversation_state.step not in ['start', 'saudacao_feita']:
                        # Reset para nova conversa
                        conversation_state.step = 'start'
                        conversation_state.temp_date = None
                        conversation_state.temp_time = None
                        conversation_state.temp_type = None
                        conversation_state.save()
                    
                    # FLUXO DE CONVERSA HUMANIZADA COM ELÔ
                    if conversation_state.step == 'start':
                        if eh_saudacao(content) and not eh_agendamento(content):
                            # Resposta de boas-vindas cordial
                            conversation_state.step = 'saudacao_feita'
                            conversation_state.save()
                            resposta = "Oi, tudo bem? 🌸 Eu sou a Elô, secretária da Dra. Elisa Munaretti. Que bom receber sua mensagem!\n\nEstou aqui para te orientar sobre como funcionam as consultas com a Dra. Elisa, que tem mais de 20 anos de experiência cuidando da saúde mental de forma integrativa, agendamentos, valores e tudo mais que precisar.\n\nVocê gostaria de marcar um horário ou prefere saber um pouco mais antes? 💛"
                        elif eh_agendamento(content):
                            # Extrai data/hora se mencionada
                            data, hora = self.extrair_data_hora(content)
                            logger.info(f"Extraindo data/hora de '{content}': data={data}, hora={hora}")
                            if data and hora:
                                conversation_state.temp_date = data
                                conversation_state.temp_time = datetime.strptime(f'{hora}:00', '%H:%M').time()
                                conversation_state.step = 'awaiting_type'
                                conversation_state.save()
                                resposta = f"Perfeito! Vou ajudá-lo a agendar sua consulta para {data.strftime('%d/%m/%Y')} às {hora}h 🗓\n\nPara finalizar, me conta: que tipo de acompanhamento você está buscando? (primeira consulta, retorno, etc.)"
                            else:
                                conversation_state.step = 'awaiting_date_time'
                                conversation_state.save()
                                resposta = "Que bom que você quer marcar uma consulta! 🌸\n\nPara verificar a disponibilidade da Dra. Elisa, preciso saber:\n📅 Qual data seria ideal para você?\n🕐 E que horário prefere?\n\nPode me falar algo como 'amanhã às 14h' ou uma data específica como '20/06/2025 às 15h'."
                        else:
                            # Resposta geral para outras mensagens
                            resposta = "Oi! 🌸 Sou a Elô, secretária da Dra. Elisa Munaretti. Como posso te ajudar hoje? Posso auxiliar com agendamentos, informações sobre consultas ou tirar suas dúvidas 💛"
                    
                    elif conversation_state.step == 'saudacao_feita':
                        if eh_agendamento(content):
                            data, hora = self.extrair_data_hora(content)
                            if data and hora:
                                conversation_state.temp_date = data
                                conversation_state.temp_time = datetime.strptime(f'{hora}:00', '%H:%M').time()
                                conversation_state.step = 'awaiting_type'
                                conversation_state.save()
                                resposta = f"Perfeito! Vou organizar sua consulta para {data.strftime('%d/%m/%Y')} às {hora}h 🗓\n\nPara finalizar, me conta: é sua primeira vez com a Dra. Elisa ou já é um retorno?"
                            else:
                                conversation_state.step = 'awaiting_date_time'
                                conversation_state.save()
                                resposta = "Perfeito! Vou te ajudar com o agendamento ��\n\nQual data e horário seriam ideais para você? Pode me falar algo como 'amanhã às 14h' ou uma data específica."
                        else:
                            resposta = "Fico feliz em poder te ajudar! 🌸\n\nVocê gostaria de:\n• Agendar uma consulta 📅\n• Saber sobre valores e formas de pagamento 💳\n• Conhecer mais sobre o trabalho da Dra. Elisa 👩‍⚕️\n• Outras informações\n\nMe conta o que seria mais útil para você agora!"
                    
                    elif conversation_state.step == 'awaiting_date_time':
                        data, hora = self.extrair_data_hora(content)
                        if data and hora:
                            conversation_state.temp_date = data
                            conversation_state.temp_time = datetime.strptime(f'{hora}:00', '%H:%M').time()
                            conversation_state.step = 'awaiting_type'
                            conversation_state.save()
                            resposta = f"Ótimo! Anotei aqui: {data.strftime('%d/%m/%Y')} às {hora}h 🗓\n\nPara finalizar seu agendamento, me conta: é sua primeira consulta com a Dra. Elisa ou você já é paciente?"
                        else:
                            resposta = "Não consegui identificar a data e horário específicos. Poderia me ajudar enviando de forma mais clara?\n\nPor exemplo:\n• 'Amanhã às 14h'\n• '20/06/2025 às 15h'\n• 'Segunda-feira às 10h'\n\nEstou aqui para te ajudar! 💛"
                    
                    elif conversation_state.step == 'awaiting_type':
                        conversation_state.temp_type = content.strip()
                        # Criar agendamento
                        try:
                            appointment = Appointment.objects.create(
                                client=appointment_client,
                                date_time=datetime.combine(conversation_state.temp_date, conversation_state.temp_time),
                                description=conversation_state.temp_type or 'Consulta',
                                status='scheduled'
                            )
                            resposta = f"🌸 Agendamento confirmado! 🌸\n\nSua consulta com a Dra. Elisa está marcada para:\n📅 {appointment.date_time.strftime('%d/%m/%Y às %H:%M')}\n📝 {appointment.description}\n\nO valor da consulta é R$ 620,00. Pode ser pago via Pix, transferência ou parcelado em até 12x no cartão.\n\nUm dia antes, vou te lembrar com todos os detalhes. Qualquer dúvida, é só me chamar por aqui. Estou por perto 💛"
                            conversation_state.step = 'completed'
                            conversation_state.save()
                        except Exception as e:
                            logger.error(f"Erro ao criar agendamento: {str(e)}")
                            resposta = "Ops! Tive um probleminha técnico ao confirmar seu agendamento. Poderia tentar novamente? Se persistir, me chama que resolvo rapidinho! 💛"
                    
                    elif conversation_state.step == 'completed':
                        if 'novo agendamento' in content.lower() or eh_agendamento(content):
                            conversation_state.step = 'start'
                            conversation_state.temp_date = None
                            conversation_state.temp_time = None
                            conversation_state.temp_type = None
                            conversation_state.save()
                            resposta = "Claro! Vou te ajudar com um novo agendamento 🌸\n\nQual data e horário você tem em mente para esta nova consulta?"
                        else:
                            resposta = "Oi! Seu agendamento anterior já está confirmado 🗓\n\nPrecisa de alguma coisa? Posso ajudar com:\n• Novo agendamento\n• Informações sobre a consulta\n• Dúvidas sobre pagamento\n• Outras questões\n\nQualquer coisa, é só me chamar! 💛"

                    if resposta:
                        # Envia a resposta e salva no banco
                        result = self.send_message(phone, resposta)
                        WhatsAppMessage.objects.create(
                            client=auth_client,
                            content=resposta,
                            message_type='SENT',
                            direction='SENT',
                            message_id=result.get('id', '')
                        )
                        logger.info('Mensagem de resposta salva no banco')
                        return  # Não chama IA se for fluxo de agendamento
                else:
                    logger.info("Mensagem não é de conversação, tipo: %s", message_type)

        except Exception as e:
            logger.error("Erro ao processar webhook: %s", str(e))
            raise 

    def extrair_data_hora(self, texto):
        # Melhor extração de data e hora
        texto = texto.lower().replace('ã', 'a').replace('ç', 'c')  # Remove acentos
        hoje = datetime.now().date()
        
        # Detecta data
        data = None
        if any(palavra in texto for palavra in ['amanha', 'amanhã']):
            data = hoje + timedelta(days=1)
        elif 'hoje' in texto:
            data = hoje
        else:
            # Tenta extrair data no formato dd/mm/yyyy
            data_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', texto)
            if data_match:
                try:
                    data = datetime.strptime(data_match.group(1), '%d/%m/%Y').date()
                except:
                    data = None
        
        # Detecta hora - aceita vários formatos
        hora = None
        # Padrões: "14h", "às 14h", "as 14", "14:00", "14 horas"
        hora_patterns = [
            r'(\d{1,2})h',           # 14h
            r'as (\d{1,2})',         # as 14
            r'às (\d{1,2})',         # às 14
            r'(\d{1,2}):(\d{2})',    # 14:00
            r'(\d{1,2}) horas'       # 14 horas
        ]
        
        for pattern in hora_patterns:
            hora_match = re.search(pattern, texto)
            if hora_match:
                hora = int(hora_match.group(1))
                break
        
        return data, hora 