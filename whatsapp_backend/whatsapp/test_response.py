import logging

logger = logging.getLogger(__name__)

class TestAIService:
    def process_message(self, message: str, context: dict = None) -> str:
        """
        Processa uma mensagem e retorna uma resposta de teste
        """
        try:
            # Log usando formatação correta
            logger.info("Processando mensagem: %s", message)
            
            # Resposta fixa para teste
            return "Olá! Esta é uma resposta de teste."
            
        except Exception as e:
            logger.error("Erro ao processar mensagem com IA: %s", str(e))
            return "Desculpe, ocorreu um erro ao processar sua mensagem."

    def generate_reminder_message(self, appointment):
        """
        Gera uma mensagem de lembrete pré-definida.
        """
        return f"""Olá! Aqui é a Elô, sua assistente virtual.
        
        Vim lembrar você da sua consulta agendada para {appointment.date_time.strftime('%d/%m/%Y às %H:%M')}.
        
        Por favor, confirme sua presença respondendo 'confirmo'.
        
        Se precisar remarcar, é só me avisar!""" 