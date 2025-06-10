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

    def send_message(self, whatsapp_number, message, media_url=None):
        """
        Envia uma mensagem via WhatsApp usando a Evolution API.
        """
        try:
            # Remove o '@s.whatsapp.net' se existir no número
            whatsapp_number = whatsapp_number.replace('@s.whatsapp.net', '')
            
            endpoint = f"{self.base_url}/message/sendText/{self.instance_id}"
            
            payload = {
                "number": whatsapp_number,
                "text": message
            }

            if media_url:
                endpoint = f"{self.base_url}/message/sendMedia/{self.instance_id}"
                payload["media_url"] = media_url

            logger.info(f"Enviando mensagem para {whatsapp_number}: {message}")
            logger.info(f"Endpoint: {endpoint}")
            logger.info(f"Payload: {json.dumps(payload)}")
            
            response = requests.post(
                endpoint,
                headers=self.headers,
                json=payload
            )

            response_data = response.json()
            
            # Verifica se a resposta indica erro
            if response.status_code == 404 or (isinstance(response_data, dict) and response_data.get('error')):
                logger.error(f"Erro ao enviar mensagem: {response.text}")
                raise ValidationError(f"Erro ao enviar mensagem: {response.text}")

            logger.info(f"Mensagem enviada com sucesso: {response.text}")
            return response_data

        except Exception as e:
            logger.error(f"Erro no serviço Evolution API: {str(e)}")
            raise

    def process_webhook(self, payload):
        """
        Processa o webhook recebido da Evolution API.
        """
        try:
            # Implementar lógica de processamento do webhook
            # Este é apenas um exemplo básico
            if 'message' in payload:
                message = payload['message']
                return {
                    'whatsapp_number': message.get('from'),
                    'content': message.get('content'),
                    'type': message.get('type'),
                    'timestamp': message.get('timestamp')
                }
            return None

        except Exception as e:
            logger.error(f"Erro ao processar webhook: {str(e)}")
            raise

    def get_connection_status(self):
        """
        Verifica o status da conexão com o WhatsApp.
        """
        try:
            response = requests.get(
                f"{self.base_url}/status",
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao verificar status: {str(e)}")
            raise

    def disconnect(self):
        """
        Desconecta a sessão do WhatsApp.
        """
        try:
            response = requests.delete(
                f"{self.base_url}/disconnect",
                headers=self.headers
            )
            return response.json()
        except Exception as e:
            logger.error(f"Erro ao desconectar: {str(e)}")
            raise 