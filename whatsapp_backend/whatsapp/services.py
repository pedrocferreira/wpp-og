import requests
from django.conf import settings
from django.core.exceptions import ValidationError
import json
import logging

logger = logging.getLogger(__name__)

class EvolutionAPIService:
    def __init__(self):
        self.base_url = settings.EVOLUTION_API_URL
        self.api_key = settings.EVOLUTION_API_KEY
        self.instance_id = settings.EVOLUTION_INSTANCE_ID
        self.headers = {
            'Content-Type': 'application/json',
            'apikey': self.api_key
        }

    def send_message(self, whatsapp_number: str, message: str, media_url: str = None):
        """Envia uma mensagem via Evolution API"""
        try:
            # Remove o '@s.whatsapp.net' se existir no número
            whatsapp_number = whatsapp_number.replace('@s.whatsapp.net', '')
            
            endpoint = f"{self.base_url}/message/sendText/{self.instance_id}"
            
            payload = {
                "number": whatsapp_number,
                "text": message,
                "linkPreview": True  # Habilita preview de links se houver
            }
            
            # Log usando formatação correta
            logger.info("Enviando mensagem para %s: %s", whatsapp_number, message)
            logger.info("Endpoint: %s", endpoint)
            logger.info("Payload: %s", json.dumps(payload))
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload
            )
            
            if not response.ok:
                logger.error("Erro ao enviar mensagem: %s", response.text)
                raise ValidationError(response.text)
            
            logger.info("Mensagem enviada com sucesso: %s", response.text)
            return response.json()
            
        except Exception as e:
            logger.error("Erro no serviço Evolution API: %s", str(e))
            raise

    def process_webhook(self, data: dict):
        """Processa um webhook recebido"""
        try:
            # Implementar lógica de processamento do webhook
            # Este é apenas um exemplo básico
            if 'message' in data:
                message = data['message']
                return {
                    'whatsapp_number': message.get('from'),
                    'content': message.get('content'),
                    'type': message.get('type'),
                    'timestamp': message.get('timestamp')
                }
            return None

        except Exception as e:
            logger.error("Erro ao processar webhook: %s", str(e))
            raise

    def get_connection_status(self):
        """Verifica o status da conexão"""
        try:
            response = requests.get(
                f"{self.base_url}/status",
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            logger.error("Erro ao verificar status: %s", str(e))
            raise

    def disconnect(self):
        """Desconecta a sessão do WhatsApp"""
        try:
            response = requests.delete(
                f"{self.base_url}/disconnect",
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            logger.error("Erro ao desconectar: %s", str(e))
            raise 