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
            
            # Log usando formatação correta
            logger.info("Enviando mensagem para %s: %s", phone, message)
            logger.info("URL: %s", url)
            logger.info("Data: %s", json.dumps(data))
            
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            
            logger.info("Mensagem enviada com sucesso para %s", phone)
            return response.json()
            
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
                    'name': name or phone,
                    'phone': phone
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

    def process_webhook(self, data):
        try:
            # Log usando json.dumps para objetos complexos
            logger.info("Processando webhook: %s", json.dumps(data))
            
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
                    logger.error("Número do cliente não encontrado")
                    return None

                # Processa a mensagem - agora lidando com o novo formato
                message_content = message_data.get('message', {}).get('conversation', '')
                if not message_content and message_data.get('message'):
                    # Tenta outros campos possíveis de mensagem
                    message_obj = message_data.get('message', {})
                    if 'extendedTextMessage' in message_obj:
                        message_content = message_obj['extendedTextMessage'].get('text', '')
                    elif 'imageMessage' in message_obj:
                        message_content = message_obj['imageMessage'].get('caption', 'Imagem recebida')
                    elif 'videoMessage' in message_obj:
                        message_content = message_obj['videoMessage'].get('caption', 'Vídeo recebido')
                    elif 'documentMessage' in message_obj:
                        message_content = message_obj['documentMessage'].get('fileName', 'Documento recebido')
                    elif 'audioMessage' in message_obj:
                        message_content = 'Áudio recebido'
                    elif 'stickerMessage' in message_obj:
                        message_content = 'Sticker recebido'

                if not message_content:
                    logger.info("Mensagem sem conteúdo")
                    return None

                # Busca ou cria o cliente
                client = self._get_or_create_client(client_number, message_data.get('pushName', ''))
                
                # Cria a mensagem
                whatsapp_message = WhatsAppMessage.objects.create(
                    client=client,
                    content=message_content,
                    direction='RECEIVED',
                    message_id=message_data.get('key', {}).get('id', '')
                )
                
                # Log usando json.dumps para objetos complexos
                log_data = {
                    'id': whatsapp_message.id,
                    'client': client_number,
                    'content': message_content
                }
                logger.info("Mensagem processada com sucesso: %s", json.dumps(log_data))
                return whatsapp_message

        except Exception as e:
            error_msg = str(e)
            logger.error("Erro ao processar webhook: %s", error_msg)
            raise Exception(error_msg) 