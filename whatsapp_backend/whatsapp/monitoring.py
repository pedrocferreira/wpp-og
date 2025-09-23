import logging
import time
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from .models import WhatsAppMessage, EvolutionConfig
from .tasks import health_check_evolution_api
from typing import Dict, Any, List
import requests

logger = logging.getLogger(__name__)


class WhatsAppMonitor:
    """
    Sistema de monitoramento para WhatsApp com alertas e métricas
    """
    
    def __init__(self):
        self.cache_timeout = 300  # 5 minutos
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Verifica saúde geral do sistema WhatsApp
        """
        try:
            health_data = {
                'timestamp': timezone.now().isoformat(),
                'overall_status': 'healthy',
                'components': {}
            }
            
            # Verifica Evolution API
            evolution_status = self._check_evolution_api()
            health_data['components']['evolution_api'] = evolution_status
            
            # Verifica filas Celery
            celery_status = self._check_celery_queues()
            health_data['components']['celery'] = celery_status
            
            # Verifica performance de mensagens
            message_stats = self._get_message_performance()
            health_data['components']['messages'] = message_stats
            
            # Verifica Redis
            redis_status = self._check_redis()
            health_data['components']['redis'] = redis_status
            
            # Define status geral
            failed_components = [
                comp for comp in health_data['components'].values() 
                if comp.get('status') != 'healthy'
            ]
            
            if failed_components:
                health_data['overall_status'] = 'degraded' if len(failed_components) < 2 else 'unhealthy'
            
            logger.info(f"[MONITOR] Status geral: {health_data['overall_status']}")
            return health_data
            
        except Exception as e:
            logger.error(f"[MONITOR] Erro ao verificar saúde do sistema: {str(e)}")
            return {
                'timestamp': timezone.now().isoformat(),
                'overall_status': 'error',
                'error': str(e)
            }
    
    def _check_evolution_api(self) -> Dict[str, Any]:
        """Verifica status da Evolution API"""
        try:
            config = EvolutionConfig.objects.filter(is_active=True).first()
            if not config:
                return {
                    'status': 'error',
                    'message': 'Nenhuma configuração ativa encontrada'
                }
            
            headers = {
                "Content-Type": "application/json",
                "apikey": config.api_key
            }
            
            url = f"{settings.EVOLUTION_API_URL}/instance/connectionState/{config.instance_id}"
            
            start_time = time.time()
            response = requests.get(url, headers=headers, timeout=10)
            response_time = (time.time() - start_time) * 1000  # em ms
            
            response.raise_for_status()
            result = response.json()
            
            is_connected = result.get('instance', {}).get('state') == 'open'
            
            return {
                'status': 'healthy' if is_connected else 'unhealthy',
                'connected': is_connected,
                'response_time_ms': round(response_time, 2),
                'instance_id': config.instance_id,
                'last_check': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[MONITOR] Erro ao verificar Evolution API: {str(e)}")
            return {
                'status': 'error',
                'message': str(e),
                'response_time_ms': None
            }
    
    def _check_celery_queues(self) -> Dict[str, Any]:
        """Verifica status das filas Celery"""
        try:
            from celery import current_app
            
            inspect = current_app.control.inspect()
            active_tasks = inspect.active() or {}
            scheduled_tasks = inspect.scheduled() or {}
            stats = inspect.stats() or {}
            
            total_active = sum(len(tasks) for tasks in active_tasks.values())
            total_scheduled = sum(len(tasks) for tasks in scheduled_tasks.values())
            workers = list(active_tasks.keys())
            
            # Calcula tarefas por worker
            worker_stats = {}
            for worker in workers:
                worker_stats[worker] = {
                    'active_tasks': len(active_tasks.get(worker, [])),
                    'total_tasks': stats.get(worker, {}).get('total', 0)
                }
            
            status = 'healthy'
            if total_active > 100:  # Muitas tarefas ativas
                status = 'degraded'
            elif total_active > 200:
                status = 'unhealthy'
            
            return {
                'status': status,
                'active_tasks': total_active,
                'scheduled_tasks': total_scheduled,
                'workers': workers,
                'worker_count': len(workers),
                'worker_stats': worker_stats,
                'last_check': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[MONITOR] Erro ao verificar Celery: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _get_message_performance(self) -> Dict[str, Any]:
        """Analisa performance das mensagens"""
        try:
            now = timezone.now()
            last_hour = now - timedelta(hours=1)
            last_24h = now - timedelta(hours=24)
            
            # Estatísticas da última hora
            hour_sent = WhatsAppMessage.objects.filter(
                timestamp__gte=last_hour,
                message_type='SENT'
            ).count()
            
            hour_received = WhatsAppMessage.objects.filter(
                timestamp__gte=last_hour,
                message_type='RECEIVED'
            ).count()
            
            hour_failed = WhatsAppMessage.objects.filter(
                timestamp__gte=last_hour,
                status='failed'
            ).count()
            
            # Estatísticas das últimas 24h
            daily_sent = WhatsAppMessage.objects.filter(
                timestamp__gte=last_24h,
                message_type='SENT'
            ).count()
            
            daily_received = WhatsAppMessage.objects.filter(
                timestamp__gte=last_24h,
                message_type='RECEIVED'
            ).count()
            
            daily_failed = WhatsAppMessage.objects.filter(
                timestamp__gte=last_24h,
                status='failed'
            ).count()
            
            # Calcula taxa de sucesso
            total_attempts = daily_sent + daily_failed
            success_rate = ((daily_sent / total_attempts) * 100) if total_attempts > 0 else 100
            
            # Define status baseado na performance
            status = 'healthy'
            if success_rate < 95:
                status = 'degraded'
            elif success_rate < 85:
                status = 'unhealthy'
            
            return {
                'status': status,
                'last_hour': {
                    'sent': hour_sent,
                    'received': hour_received,
                    'failed': hour_failed
                },
                'last_24h': {
                    'sent': daily_sent,
                    'received': daily_received,
                    'failed': daily_failed,
                    'success_rate': round(success_rate, 2)
                },
                'last_check': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[MONITOR] Erro ao analisar performance: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def _check_redis(self) -> Dict[str, Any]:
        """Verifica status do Redis"""
        try:
            import redis
            
            redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
            
            start_time = time.time()
            redis_client.ping()
            response_time = (time.time() - start_time) * 1000
            
            info = redis_client.info()
            used_memory = info.get('used_memory_human', 'N/A')
            connected_clients = info.get('connected_clients', 0)
            
            return {
                'status': 'healthy',
                'response_time_ms': round(response_time, 2),
                'used_memory': used_memory,
                'connected_clients': connected_clients,
                'last_check': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"[MONITOR] Erro ao verificar Redis: {str(e)}")
            return {
                'status': 'error',
                'message': str(e)
            }
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Gera alertas baseados em métricas do sistema
        """
        alerts = []
        
        try:
            health = self.get_system_health()
            
            # Alerta para Evolution API
            evolution = health['components'].get('evolution_api', {})
            if evolution.get('status') != 'healthy':
                alerts.append({
                    'type': 'critical',
                    'component': 'evolution_api',
                    'message': 'Evolution API não está funcionando corretamente',
                    'details': evolution,
                    'timestamp': timezone.now().isoformat()
                })
            
            # Alerta para filas Celery
            celery = health['components'].get('celery', {})
            if celery.get('active_tasks', 0) > 50:
                alerts.append({
                    'type': 'warning',
                    'component': 'celery',
                    'message': f"Muitas tarefas na fila: {celery.get('active_tasks')}",
                    'details': celery,
                    'timestamp': timezone.now().isoformat()
                })
            
            # Alerta para mensagens falhadas
            messages = health['components'].get('messages', {})
            success_rate = messages.get('last_24h', {}).get('success_rate', 100)
            if success_rate < 90:
                alerts.append({
                    'type': 'warning' if success_rate > 80 else 'critical',
                    'component': 'messages',
                    'message': f"Taxa de sucesso baixa: {success_rate}%",
                    'details': messages,
                    'timestamp': timezone.now().isoformat()
                })
            
            # Alerta para Redis
            redis_status = health['components'].get('redis', {})
            if redis_status.get('status') != 'healthy':
                alerts.append({
                    'type': 'critical',
                    'component': 'redis',
                    'message': 'Redis não está respondendo',
                    'details': redis_status,
                    'timestamp': timezone.now().isoformat()
                })
            
            return alerts
            
        except Exception as e:
            logger.error(f"[MONITOR] Erro ao gerar alertas: {str(e)}")
            return [{
                'type': 'critical',
                'component': 'monitor',
                'message': f'Erro no sistema de monitoramento: {str(e)}',
                'timestamp': timezone.now().isoformat()
            }]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Coleta métricas detalhadas de performance
        """
        try:
            cache_key = 'whatsapp_performance_metrics'
            cached_metrics = cache.get(cache_key)
            
            if cached_metrics:
                return cached_metrics
            
            now = timezone.now()
            periods = {
                'last_hour': now - timedelta(hours=1),
                'last_6h': now - timedelta(hours=6),
                'last_24h': now - timedelta(hours=24),
                'last_week': now - timedelta(days=7)
            }
            
            metrics = {
                'timestamp': now.isoformat(),
                'periods': {}
            }
            
            for period_name, start_time in periods.items():
                # Mensagens por período
                sent_count = WhatsAppMessage.objects.filter(
                    timestamp__gte=start_time,
                    message_type='SENT'
                ).count()
                
                received_count = WhatsAppMessage.objects.filter(
                    timestamp__gte=start_time,
                    message_type='RECEIVED'
                ).count()
                
                failed_count = WhatsAppMessage.objects.filter(
                    timestamp__gte=start_time,
                    status='failed'
                ).count()
                
                # Taxa de resposta (sent/received)
                response_rate = (sent_count / received_count * 100) if received_count > 0 else 0
                
                metrics['periods'][period_name] = {
                    'messages_sent': sent_count,
                    'messages_received': received_count,
                    'messages_failed': failed_count,
                    'response_rate': round(response_rate, 2),
                    'success_rate': round((sent_count / (sent_count + failed_count) * 100) if (sent_count + failed_count) > 0 else 100, 2)
                }
            
            # Cache por 5 minutos
            cache.set(cache_key, metrics, self.cache_timeout)
            
            return metrics
            
        except Exception as e:
            logger.error(f"[MONITOR] Erro ao coletar métricas: {str(e)}")
            return {
                'timestamp': timezone.now().isoformat(),
                'error': str(e)
            } 