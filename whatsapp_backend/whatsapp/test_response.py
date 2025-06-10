import logging

logger = logging.getLogger(__name__)

class TestAIService:
    def process_message(self, message: str, context: dict = None) -> dict:
        """
        Processa uma mensagem e retorna uma resposta de teste
        """
        try:
            logger.info(f"Processando mensagem: {message}")
            
            # Resposta padrão de teste
            return {
                'response_text': f"Olá! Recebi sua mensagem: '{message}'. Este é um teste do sistema.",
                'confidence_score': 1.0,
                'intent_detected': 'test_response'
            }
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem com IA: {str(e)}")
            return {
                'response_text': "Desculpe, tive um problema ao processar sua mensagem.",
                'confidence_score': 0.0,
                'intent_detected': 'error'
            }

    def generate_reminder_message(self, appointment):
        """
        Gera uma mensagem de lembrete pré-definida.
        """
        return f"""Olá! Aqui é a Elô, sua assistente virtual.
        
        Vim lembrar você da sua consulta agendada para {appointment.date_time.strftime('%d/%m/%Y às %H:%M')}.
        
        Por favor, confirme sua presença respondendo 'confirmo'.
        
        Se precisar remarcar, é só me avisar!""" 