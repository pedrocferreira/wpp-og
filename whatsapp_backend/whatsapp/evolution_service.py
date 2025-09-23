import requests
import json
import logging
from django.conf import settings
from .models import EvolutionConfig, WhatsAppMessage
from authentication.models import Client as AuthClient
from datetime import datetime, timedelta
import re
from appointments.models import Appointment
from authentication.models import Client as AppointmentClient

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
        """
        Envia mensagem via Evolution API de forma assíncrona (OTIMIZADO)
        Para casos urgentes onde é necessário resposta imediata, use send_message_sync()
        """
        try:
            # Importa o serviço assíncrono
            from .async_message_service import AsyncMessageService
            
            async_service = AsyncMessageService()
            
            # Envia de forma assíncrona por padrão
            result = async_service.send_message_async(
                phone=phone,
                message=message,
                media_url=media_url,
                client_whatsapp=phone,
                priority='normal'
            )
            
            logger.info("Mensagem agendada assincronamente para %s (task: %s)", 
                       phone, result.get('task_id'))
            
            return result
            
        except Exception as e:
            logger.error("Erro ao agendar mensagem assíncrona: %s", str(e))
            return None
    
    def send_message_sync(self, phone: str, message: str, media_url: str = None):
        """
        Envia mensagem de forma síncrona (usar apenas quando necessário)
        """
        url = f"{self.base_url}/message/sendText/{self.config.instance_id}"
        
        data = {
            "number": phone,
            "text": message,
            "linkPreview": True
        }
        
        if media_url:
            data["mediaUrl"] = media_url
            
        logger.info("Enviando mensagem SÍNCRONA para %s: %s", phone, message[:100])
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.info("Mensagem síncrona enviada com sucesso para %s", phone)
            return result
        except requests.exceptions.RequestException as e:
            logger.error("Erro ao enviar mensagem síncrona: %s", str(e))
            if hasattr(e, 'response') and e.response is not None:
                logger.error("Resposta de erro: %s", e.response.text)
            return None

    def _get_or_create_client(self, phone: str, name: str = None) -> AuthClient:
        """Busca ou cria um cliente na tabela de autenticação"""
        client, created = AuthClient.objects.get_or_create(
            whatsapp=phone,
            defaults={
                'name': name or f'Cliente {phone}',
                'email': ''
            }
        )
        if created:
            logger.info("Novo cliente criado: %s", client.whatsapp)
        return client

    def process_webhook(self, data: dict):
        """Processa webhook do Evolution API usando SmartAI"""
        try:
            # Verifica se há webhook key nos headers
            webhook_headers = data.get('headers', {})
            if webhook_headers.get('apikey'):
                self.headers['apikey'] = webhook_headers['apikey']
                self.headers['token'] = webhook_headers['apikey']
                logger.info("Headers atualizados com a chave do webhook: %s", json.dumps(self.headers))

            # Processa o evento principal
            event = data.get('event')
            logger.info("Processando webhook: %s", json.dumps(data))
            
            if event == 'messages.upsert':
                logger.info("Evento messages.upsert detectado")
                
                message_data = data.get('data', {})
                key = message_data.get('key', {})
                message = message_data.get('message', {})
                message_type = message_data.get('messageType', '')
                
                logger.info("Key extraída: %s", json.dumps(key))
                logger.info("Message extraída: %s", json.dumps(message))
                logger.info("MessageType: %s", message_type)
                
                if message_type == 'conversation' and not key.get('fromMe', False):
                    logger.info("Mensagem de conversação detectada")
                    
                    # Extrai informações da mensagem
                    phone = key.get('remoteJid', '').replace('@s.whatsapp.net', '')
                    content = message.get('conversation', '')
                    push_name = message_data.get('pushName', '')
                    
                    logger.info("Conteúdo da mensagem: %s", content)
                    logger.info("Número do telefone extraído: %s", phone)
                    
                    if not phone or not content:
                        logger.warning("Mensagem inválida - faltam dados obrigatórios")
                        return
                    
                    # Cria/busca cliente na tabela de autenticação
                    auth_client = self._get_or_create_client(phone, push_name)
                    
                    # Cria/busca cliente na tabela de agendamentos
                    appointment_client, created = AppointmentClient.objects.get_or_create(
                        whatsapp=phone,
                        defaults={'name': push_name or auth_client.name}
                    )
                    logger.info("Cliente encontrado: %s", appointment_client.whatsapp)

                    # Salva a mensagem no banco
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
                    
                    # Prepara o contexto para o SmartAI
                    context = {
                        'client': appointment_client,  # Cliente da tabela appointments
                        'auth_client': auth_client,    # Cliente da tabela authentication
                        'client_id': auth_client.id,
                        'conversation_history': list(reversed(conversation_history))  # Inverte para ordem cronológica
                    }
                    
                    # Processa mensagem com SmartAI
                    logger.info("Processando mensagem com SmartAI: %s", content)
                    resposta = self.ai_service.process_message(
                        message_text=content, 
                        client_whatsapp=phone, 
                        client_name=push_name or appointment_client.name
                    )
                    
                    # Envia resposta e salva no banco
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
                        return
                        
                else:
                    logger.info("Mensagem não é de conversação, tipo: %s", message_type)

        except Exception as e:
            logger.error("Erro ao processar webhook: %s", str(e))
            raise 