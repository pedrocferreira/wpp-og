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
            "apikey": self.config.api_key
        }

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
            
            logger.info(f"Enviando mensagem para {phone}: {message}")
            logger.info(f"URL: {url}")
            logger.info(f"Data: {json.dumps(data)}")
            
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            logger.info(f"Mensagem enviada com sucesso para {phone}")
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar mensagem: {str(e)}")
            raise

    def process_webhook(self, data: dict) -> dict:
        """Processa os dados recebidos do webhook"""
        try:
            logger.info(f"Processando webhook: {json.dumps(data)}")
            
            # Verifica se é uma mensagem recebida
            if data.get('event') == 'messages.upsert' and 'data' in data:
                message_data = data['data']
                
                # Ignora mensagens enviadas pelo próprio bot
                if message_data.get('key', {}).get('fromMe', False):
                    logger.info("Ignorando mensagem enviada pelo bot")
                    return None
                
                # Extrai o número do remetente
                client_number = message_data.get('key', {}).get('remoteJid', '').split('@')[0]
                
                if not client_number:
                    logger.error("Número do cliente não encontrado na mensagem")
                    return None

                # Extrai o conteúdo da mensagem
                content = None
                message = message_data.get('message', {})
                
                if 'conversation' in message:
                    content = message['conversation']
                elif 'extendedTextMessage' in message:
                    content = message['extendedTextMessage'].get('text')
                elif 'imageMessage' in message:
                    content = message['imageMessage'].get('caption', 'Imagem recebida')
                elif 'videoMessage' in message:
                    content = message['videoMessage'].get('caption', 'Vídeo recebido')
                elif 'audioMessage' in message:
                    content = 'Áudio recebido'
                elif 'documentMessage' in message:
                    content = 'Documento recebido'
                
                if not content:
                    logger.error("Conteúdo da mensagem não encontrado")
                    return None
                
                # Criar ou obter cliente
                client, _ = Client.objects.get_or_create(
                    whatsapp=client_number,
                    defaults={"name": f"Cliente {client_number}"}
                )
                
                # Criar mensagem
                whatsapp_message = WhatsAppMessage.objects.create(
                    client=client,
                    message_type="incoming",
                    content=content,
                    status='received'
                )
                
                logger.info(f"Mensagem processada com sucesso: {whatsapp_message.id}")
                return whatsapp_message
            
            return None
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook: {str(e)}")
            return None 