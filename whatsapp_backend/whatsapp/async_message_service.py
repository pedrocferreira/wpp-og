import logging
import requests
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.cache import cache
from .tasks import send_whatsapp_message_async, send_delayed_message_async
from .models import EvolutionConfig
from authentication.models import Client as AuthClient
import json

logger = logging.getLogger(__name__)


class AsyncMessageService:
    """
    Serviço otimizado para envio de mensagens WhatsApp usando filas assíncronas
    """
    
    def __init__(self):
        self.config = self._get_config()
    
    def _get_config(self) -> Optional[EvolutionConfig]:
        """Obtém configuração ativa do Evolution com cache"""
        config = cache.get('evolution_config')
        if not config:
            config = EvolutionConfig.objects.filter(is_active=True).first()
            if config:
                cache.set('evolution_config', config, 300)  # Cache por 5 minutos
        return config
    
    def send_message_async(self, phone: str, message: str, media_url: str = None, 
                          client_whatsapp: str = None, priority: str = 'normal') -> Dict[str, Any]:
        """
        Envia mensagem de forma assíncrona usando Celery
        
        Args:
            phone: Número do telefone
            message: Conteúdo da mensagem
            media_url: URL da mídia (opcional)
            client_whatsapp: WhatsApp do cliente para buscar no banco
            priority: Prioridade da mensagem ('high', 'normal', 'low')
        
        Returns:
            Dict com informações da tarefa agendada
        """
        try:
            # Busca cliente se fornecido
            client_id = None
            if client_whatsapp:
                client = AuthClient.objects.filter(whatsapp=client_whatsapp).first()
                if client:
                    client_id = client.id
            
            # Define prioridade da fila
            queue_name = 'celery'  # fila padrão
            if priority == 'high':
                queue_name = 'high_priority'
            elif priority == 'low':
                queue_name = 'low_priority'
            
            # Agenda tarefa assíncrona
            task = send_whatsapp_message_async.apply_async(
                args=[phone, message, media_url, client_id],
                queue=queue_name
            )
            
            logger.info(f"[ASYNC] Mensagem agendada para {phone} (task_id: {task.id})")
            
            return {
                'status': 'scheduled',
                'task_id': task.id,
                'phone': phone,
                'message_preview': message[:50] + '...' if len(message) > 50 else message,
                'priority': priority
            }
            
        except Exception as e:
            logger.error(f"[ASYNC] Erro ao agendar mensagem: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'phone': phone
            }
    
    def send_delayed_message(self, phone: str, message: str, delay_seconds: int = 3,
                           client_whatsapp: str = None) -> Dict[str, Any]:
        """
        Envia mensagem com delay para simular digitação humana
        """
        try:
            client_id = None
            if client_whatsapp:
                client = AuthClient.objects.filter(whatsapp=client_whatsapp).first()
                if client:
                    client_id = client.id
            
            task = send_delayed_message_async.apply_async(
                args=[phone, message, delay_seconds, client_id]
            )
            
            logger.info(f"[DELAYED] Mensagem agendada com delay de {delay_seconds}s para {phone}")
            
            return {
                'status': 'scheduled_delayed',
                'task_id': task.id,
                'phone': phone,
                'delay_seconds': delay_seconds
            }
            
        except Exception as e:
            logger.error(f"[DELAYED] Erro ao agendar mensagem delayed: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'phone': phone
            }
    
    def send_message_sync(self, phone: str, message: str, media_url: str = None) -> Optional[Dict[str, Any]]:
        """
        Envio síncrono para casos onde é necessário resposta imediata
        (usar apenas quando realmente necessário)
        """
        try:
            if not self.config:
                raise ValueError("Nenhuma configuração ativa do Evolution encontrada")
            
            headers = {
                "Content-Type": "application/json",
                "apikey": self.config.api_key,
                "token": self.config.api_key
            }
            
            url = f"{settings.EVOLUTION_API_URL}/message/sendText/{self.config.instance_id}"
            data = {
                "number": phone,
                "text": message,
                "linkPreview": True
            }
            
            if media_url:
                data["mediaUrl"] = media_url
            
            logger.info(f"[SYNC] Enviando mensagem síncrona para {phone}")
            
            response = requests.post(url, headers=headers, json=data, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"[SYNC] Mensagem síncrona enviada com sucesso para {phone}")
            
            return result
            
        except Exception as e:
            logger.error(f"[SYNC] Erro ao enviar mensagem síncrona: {str(e)}")
            return None
    
    def send_bulk_messages(self, messages: list, priority: str = 'normal') -> Dict[str, Any]:
        """
        Envia múltiplas mensagens de forma otimizada
        
        Args:
            messages: Lista de dicts com 'phone', 'message', 'media_url' (opcional)
            priority: Prioridade das mensagens
        """
        try:
            results = []
            
            for msg_data in messages:
                phone = msg_data.get('phone')
                message = msg_data.get('message')
                media_url = msg_data.get('media_url')
                client_whatsapp = msg_data.get('client_whatsapp')
                
                if not phone or not message:
                    logger.warning("[BULK] Mensagem inválida ignorada")
                    continue
                
                result = self.send_message_async(
                    phone=phone,
                    message=message,
                    media_url=media_url,
                    client_whatsapp=client_whatsapp,
                    priority=priority
                )
                results.append(result)
            
            logger.info(f"[BULK] {len(results)} mensagens agendadas")
            
            return {
                'status': 'bulk_scheduled',
                'total_messages': len(results),
                'successful': len([r for r in results if r['status'] == 'scheduled']),
                'failed': len([r for r in results if r['status'] == 'error']),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"[BULK] Erro ao agendar mensagens em lote: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Verifica status de uma tarefa específica
        """
        try:
            from celery.result import AsyncResult
            
            task = AsyncResult(task_id)
            
            return {
                'task_id': task_id,
                'status': task.status,
                'result': task.result if task.ready() else None,
                'traceback': task.traceback if task.failed() else None
            }
            
        except Exception as e:
            logger.error(f"[STATUS] Erro ao verificar status da tarefa {task_id}: {str(e)}")
            return {
                'task_id': task_id,
                'status': 'unknown',
                'error': str(e)
            }
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas das filas de mensagens
        """
        try:
            from celery import current_app
            
            inspect = current_app.control.inspect()
            active_tasks = inspect.active()
            scheduled_tasks = inspect.scheduled()
            
            stats = {
                'active_tasks': sum(len(tasks) for tasks in (active_tasks or {}).values()),
                'scheduled_tasks': sum(len(tasks) for tasks in (scheduled_tasks or {}).values()),
                'workers': list((active_tasks or {}).keys())
            }
            
            logger.info(f"[STATS] Estatísticas da fila: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"[STATS] Erro ao obter estatísticas: {str(e)}")
            return {
                'error': str(e)
            }
    
    def retry_failed_messages(self, hours: int = 24) -> Dict[str, Any]:
        """
        Reagenda mensagens que falharam nas últimas X horas
        """
        try:
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff_time = timezone.now() - timedelta(hours=hours)
            
            # Busca mensagens falhadas
            failed_messages = WhatsAppMessage.objects.filter(
                timestamp__gte=cutoff_time,
                status='failed',
                content__startswith='[FALHA]'
            )
            
            retry_count = 0
            for msg in failed_messages:
                # Remove marcador de falha
                clean_content = msg.content.replace('[FALHA] ', '')
                
                # Reagenda
                result = self.send_message_async(
                    phone=msg.client.whatsapp,
                    message=clean_content,
                    client_whatsapp=msg.client.whatsapp,
                    priority='high'
                )
                
                if result['status'] == 'scheduled':
                    retry_count += 1
                    # Marca mensagem original como processada
                    msg.status = 'retrying'
                    msg.save()
            
            logger.info(f"[RETRY] {retry_count} mensagens reagendadas")
            
            return {
                'status': 'completed',
                'retried_messages': retry_count,
                'total_failed': failed_messages.count()
            }
            
        except Exception as e:
            logger.error(f"[RETRY] Erro ao reagendar mensagens: {str(e)}")
            return {
                'status': 'error',
                'error': str(e)
            } 