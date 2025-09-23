from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import requests
import json
import logging
import time
from .models import WhatsAppMessage, EvolutionConfig
from authentication.models import Client as AuthClient
from celery.exceptions import Retry
import redis

logger = logging.getLogger(__name__)

# Pool de conexões Redis para rate limiting
redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_whatsapp_message_async(self, phone: str, message: str, media_url: str = None, client_id: int = None):
    """
    Tarefa assíncrona para envio de mensagens WhatsApp com retry automático
    """
    try:
        # Rate limiting - máximo 10 mensagens por minuto por instância
        rate_limit_key = f"whatsapp_rate_limit:{settings.EVOLUTION_INSTANCE_ID}"
        current_count = redis_client.get(rate_limit_key)
        
        if current_count and int(current_count) >= 10:
            # Se excedeu o limite, agenda para 1 minuto depois
            logger.warning(f"Rate limit atingido. Reagendando mensagem para {phone}")
            raise self.retry(countdown=60)
        
        # Incrementa contador de rate limit
        redis_client.incr(rate_limit_key)
        redis_client.expire(rate_limit_key, 60)  # Expira em 1 minuto
        
        # Obtém configuração ativa do Evolution
        config = EvolutionConfig.objects.filter(is_active=True).first()
        if not config:
            raise ValueError("Nenhuma configuração ativa do Evolution encontrada")
        
        # Prepara headers e dados
        headers = {
            "Content-Type": "application/json",
            "apikey": config.api_key,
            "token": config.api_key
        }
        
        url = f"{settings.EVOLUTION_API_URL}/message/sendText/{config.instance_id}"
        data = {
            "number": phone,
            "text": message,
            "linkPreview": True
        }
        
        if media_url:
            data["mediaUrl"] = media_url
        
        logger.info(f"[ASYNC] Enviando mensagem para {phone}: {message[:100]}...")
        
        # Envia a mensagem usando pool de conexões otimizado
        from .connection_pool import get_evolution_client
        
        evolution_client = get_evolution_client()
        result = evolution_client.send_message(phone, message, media_url)
        
        logger.info(f"[ASYNC] Mensagem enviada com sucesso para {phone} via pool otimizado")
        
        # Salva no banco se client_id foi fornecido
        if client_id:
            try:
                client = AuthClient.objects.get(id=client_id)
                WhatsAppMessage.objects.create(
                    client=client,
                    content=message,
                    message_type='SENT',
                    direction='SENT',
                    message_id=result.get('id', ''),
                    media_url=media_url
                )
                logger.info(f"[ASYNC] Mensagem salva no banco para cliente {client_id}")
            except AuthClient.DoesNotExist:
                logger.warning(f"Cliente {client_id} não encontrado para salvar mensagem")
        
        return result
        
    except requests.exceptions.RequestException as e:
        logger.error(f"[ASYNC] Erro ao enviar mensagem (tentativa {self.request.retries + 1}): {str(e)}")
        
        # Se ainda há tentativas, retry com backoff exponencial
        if self.request.retries < self.max_retries:
            countdown = (2 ** self.request.retries) * 60  # 1min, 2min, 4min
            logger.info(f"[ASYNC] Reagendando para {countdown}s")
            raise self.retry(countdown=countdown, exc=e)
        else:
            logger.error(f"[ASYNC] Falha definitiva ao enviar mensagem para {phone}: {str(e)}")
            
            # Ativa sistema de fallback
            try:
                from .fallback_service import FallbackService
                
                fallback_service = FallbackService()
                fallback_result = fallback_service.handle_api_failure(
                    phone=phone,
                    message=message,
                    media_url=media_url,
                    error=e,
                    client_id=client_id
                )
                
                logger.info(f"[ASYNC] Fallback executado: {fallback_result.get('status')}")
                
                # Se o fallback recuperou, não marca como falha definitiva
                if fallback_result.get('status') == 'recovered':
                    logger.info(f"[ASYNC] Mensagem recuperada via fallback para {phone}")
                    return fallback_result
                    
            except Exception as fallback_error:
                logger.error(f"[ASYNC] Erro no sistema de fallback: {str(fallback_error)}")
            
            # Se chegou aqui, é falha definitiva
            if client_id:
                try:
                    client = AuthClient.objects.get(id=client_id)
                    WhatsAppMessage.objects.create(
                        client=client,
                        content=f"[FALHA] {message}",
                        message_type='SENT',
                        direction='SENT',
                        status='failed',
                        media_url=media_url
                    )
                except:
                    pass
            raise
    
    except Exception as e:
        logger.error(f"[ASYNC] Erro inesperado ao enviar mensagem: {str(e)}")
        raise


@shared_task(bind=True, max_retries=2)
def send_delayed_message_async(self, phone: str, message: str, delay_seconds: int = 3, client_id: int = None):
    """
    Tarefa para envio de mensagem com delay (simula digitação humana)
    """
    try:
        logger.info(f"[DELAYED] Aguardando {delay_seconds}s antes de enviar mensagem para {phone}")
        time.sleep(delay_seconds)
        
        # Chama a tarefa de envio normal
        return send_whatsapp_message_async.delay(phone, message, None, client_id)
        
    except Exception as e:
        logger.error(f"[DELAYED] Erro ao processar mensagem delayed: {str(e)}")
        raise


@shared_task
def process_webhook_async(webhook_data: dict):
    """
    Processa webhook do Evolution de forma assíncrona
    """
    try:
        logger.info("[WEBHOOK] Processando webhook assincronamente")
        
        # Importa aqui para evitar import circular
        from .evolution_service import EvolutionService
        
        evolution_service = EvolutionService()
        result = evolution_service.process_webhook(webhook_data)
        
        logger.info("[WEBHOOK] Webhook processado com sucesso")
        return result
        
    except Exception as e:
        logger.error(f"[WEBHOOK] Erro ao processar webhook: {str(e)}")
        raise


@shared_task
def cleanup_old_messages():
    """
    Limpa mensagens antigas (mais de 30 dias) para manter performance
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = WhatsAppMessage.objects.filter(timestamp__lt=cutoff_date).delete()[0]
        
        logger.info(f"[CLEANUP] Removidas {deleted_count} mensagens antigas")
        return deleted_count
        
    except Exception as e:
        logger.error(f"[CLEANUP] Erro ao limpar mensagens antigas: {str(e)}")
        raise


@shared_task
def health_check_evolution_api():
    """
    Verifica saúde da Evolution API
    """
    try:
        config = EvolutionConfig.objects.filter(is_active=True).first()
        if not config:
            return {"status": "error", "message": "Nenhuma configuração ativa"}
        
        headers = {
            "Content-Type": "application/json",
            "apikey": config.api_key
        }
        
        url = f"{settings.EVOLUTION_API_URL}/instance/connectionState/{config.instance_id}"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        logger.info(f"[HEALTH] Evolution API Status: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[HEALTH] Erro ao verificar Evolution API: {str(e)}")
        return {"status": "error", "message": str(e)}


@shared_task
def monitor_message_queue():
    """
    Monitora fila de mensagens e gera alertas se necessário
    """
    try:
        # Verifica tamanho da fila
        inspect = send_whatsapp_message_async.app.control.inspect()
        active_tasks = inspect.active()
        
        total_tasks = sum(len(tasks) for tasks in active_tasks.values() if tasks)
        
        if total_tasks > 50:  # Alerta se mais de 50 mensagens na fila
            logger.warning(f"[MONITOR] Fila de mensagens com {total_tasks} tarefas pendentes")
        
        # Verifica mensagens falhadas nas últimas 24h
        yesterday = timezone.now() - timedelta(days=1)
        failed_messages = WhatsAppMessage.objects.filter(
            timestamp__gte=yesterday,
            status='failed'
        ).count()
        
        if failed_messages > 10:
            logger.warning(f"[MONITOR] {failed_messages} mensagens falharam nas últimas 24h")
        
        return {
            "queue_size": total_tasks,
            "failed_24h": failed_messages,
            "timestamp": timezone.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"[MONITOR] Erro ao monitorar fila: {str(e)}")
        return {"status": "error", "message": str(e)} 