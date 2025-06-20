import requests
import json
import logging
from django.conf import settings
from .models import EvolutionConfig, WhatsAppMessage
from authentication.models import Client

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
        
        # Inicializa o serviço de IA
        from .ai_service import AIService
        self.ai_service = AIService()

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

    def _get_or_create_client(self, phone: str, name: str = None) -> Client:
        """
        Busca ou cria um cliente com base no número do WhatsApp
        """
        try:
            # Remove o '@s.whatsapp.net' se existir no número
            phone = phone.replace('@s.whatsapp.net', '')
            
            # Busca ou cria o cliente
            client, created = Client.objects.get_or_create(
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
                    
                    # Busca ou cria o cliente
                    client, created = Client.objects.get_or_create(
                        whatsapp=phone,
                        defaults={
                            'name': message_data.get('pushName', 'Cliente WhatsApp'),
                            'phone': phone
                        }
                    )
                    logger.info("Cliente %s: %s", "criado" if created else "encontrado", client.whatsapp)
                    
                    # Salva a mensagem no banco
                    message_obj = WhatsAppMessage.objects.create(
                        client=client,
                        content=content,
                        message_type='RECEIVED',
                        direction='RECEIVED',
                        message_id=key.get('id', '')
                    )
                    logger.info("Mensagem processada com sucesso: %s", json.dumps({
                        'id': message_obj.id,
                        'client': client.whatsapp,
                        'content': message_obj.content
                    }))
                    
                    # Gera resposta usando o serviço de IA
                    logger.info("Gerando resposta com IA...")
                    response = self.ai_service.process_message(content, context={'client_id': client.id})
                    logger.info("Resposta gerada: %s", response)
                    
                    # Envia a resposta
                    try:
                        logger.info("Enviando resposta...")
                        result = self.send_message(phone, response)
                        logger.info("Resposta enviada com sucesso: %s", json.dumps(result))
                        
                        # Salva a mensagem de resposta
                        WhatsAppMessage.objects.create(
                            client=client,
                            content=response,
                            message_type='SENT',
                            direction='SENT',
                            message_id=result.get('id', '')
                        )
                        logger.info("Mensagem de resposta salva no banco")
                    except Exception as e:
                        logger.error("Erro ao enviar resposta: %s", str(e))
                        raise
                else:
                    logger.info("Mensagem não é de conversação, tipo: %s", message_type)
                    
        except Exception as e:
            logger.error("Erro ao processar webhook: %s", str(e))
            raise 