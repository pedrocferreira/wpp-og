import logging
import requests
from typing import Optional, Dict, Any, List
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from django.core.cache import cache
from .models import WhatsAppMessage, EvolutionConfig
from authentication.models import Client as AuthClient
import json

logger = logging.getLogger(__name__)


class FallbackService:
    """
    Serviço de fallback para quando a Evolution API falhar
    Implementa diferentes estratégias de recuperação
    """
    
    def __init__(self):
        self.fallback_strategies = [
            self._try_alternative_endpoint,
            self._queue_for_retry,
            self._notify_admin,
            self._log_for_manual_processing
        ]
    
    def handle_api_failure(self, phone: str, message: str, media_url: str = None, 
                          error: Exception = None, client_id: int = None) -> Dict[str, Any]:
        """
        Executa estratégias de fallback quando a Evolution API falha
        """
        try:
            logger.warning(f"[FALLBACK] Evolution API falhou para {phone}. Iniciando fallback...")
            
            fallback_result = {
                'original_error': str(error) if error else 'Unknown error',
                'phone': phone,
                'message_preview': message[:50] + '...' if len(message) > 50 else message,
                'timestamp': timezone.now().isoformat(),
                'fallback_attempts': []
            }
            
            # Tenta cada estratégia de fallback
            for i, strategy in enumerate(self.fallback_strategies):
                try:
                    strategy_name = strategy.__name__
                    logger.info(f"[FALLBACK] Tentando estratégia {i+1}: {strategy_name}")
                    
                    result = strategy(phone, message, media_url, error, client_id)
                    
                    fallback_result['fallback_attempts'].append({
                        'strategy': strategy_name,
                        'success': result.get('success', False),
                        'message': result.get('message', ''),
                        'timestamp': timezone.now().isoformat()
                    })
                    
                    # Se uma estratégia funcionar, para aqui
                    if result.get('success'):
                        fallback_result['status'] = 'recovered'
                        fallback_result['successful_strategy'] = strategy_name
                        logger.info(f"[FALLBACK] Recuperação bem-sucedida com {strategy_name}")
                        break
                        
                except Exception as strategy_error:
                    logger.error(f"[FALLBACK] Estratégia {strategy_name} falhou: {str(strategy_error)}")
                    fallback_result['fallback_attempts'].append({
                        'strategy': strategy_name,
                        'success': False,
                        'error': str(strategy_error),
                        'timestamp': timezone.now().isoformat()
                    })
            
            # Se nenhuma estratégia funcionou
            if 'status' not in fallback_result:
                fallback_result['status'] = 'all_fallbacks_failed'
                logger.error(f"[FALLBACK] Todas as estratégias falharam para {phone}")
            
            # Salva log de fallback no banco
            self._save_fallback_log(fallback_result, client_id)
            
            return fallback_result
            
        except Exception as e:
            logger.error(f"[FALLBACK] Erro crítico no serviço de fallback: {str(e)}")
            return {
                'status': 'fallback_service_error',
                'error': str(e),
                'phone': phone,
                'timestamp': timezone.now().isoformat()
            }
    
    def _try_alternative_endpoint(self, phone: str, message: str, media_url: str = None, 
                                 error: Exception = None, client_id: int = None) -> Dict[str, Any]:
        """
        Estratégia 1: Tenta endpoint alternativo da Evolution API
        """
        try:
            # Tenta endpoint de instância diferente ou endpoint de backup
            config = EvolutionConfig.objects.filter(is_active=True).first()
            if not config:
                return {'success': False, 'message': 'Nenhuma configuração ativa'}
            
            # Endpoints alternativos para tentar
            alternative_endpoints = [
                f"{settings.EVOLUTION_API_URL}/message/text/{config.instance_id}",
                f"{settings.EVOLUTION_API_URL}/send-message/{config.instance_id}",
                f"{settings.EVOLUTION_API_URL}/message/send/{config.instance_id}"
            ]
            
            headers = {
                "Content-Type": "application/json",
                "apikey": config.api_key,
                "token": config.api_key
            }
            
            for endpoint in alternative_endpoints:
                try:
                    data = {
                        "number": phone,
                        "text": message,
                        "linkPreview": True
                    }
                    
                    if media_url:
                        data["mediaUrl"] = media_url
                    
                    response = requests.post(endpoint, headers=headers, json=data, timeout=15)
                    
                    if response.status_code == 200:
                        logger.info(f"[FALLBACK] Sucesso com endpoint alternativo: {endpoint}")
                        return {
                            'success': True,
                            'message': f'Enviado via endpoint alternativo: {endpoint}',
                            'response': response.json()
                        }
                        
                except requests.RequestException as endpoint_error:
                    logger.warning(f"[FALLBACK] Endpoint {endpoint} falhou: {str(endpoint_error)}")
                    continue
            
            return {'success': False, 'message': 'Todos os endpoints alternativos falharam'}
            
        except Exception as e:
            return {'success': False, 'message': f'Erro na estratégia alternativa: {str(e)}'}
    
    def _queue_for_retry(self, phone: str, message: str, media_url: str = None, 
                        error: Exception = None, client_id: int = None) -> Dict[str, Any]:
        """
        Estratégia 2: Adiciona à fila de retry com prioridade alta
        """
        try:
            from .tasks import send_whatsapp_message_async
            
            # Agenda com prioridade alta e delay maior
            task = send_whatsapp_message_async.apply_async(
                args=[phone, message, media_url, client_id],
                queue='high_priority',
                countdown=300  # 5 minutos de delay
            )
            
            logger.info(f"[FALLBACK] Mensagem reagendada com prioridade alta (task: {task.id})")
            
            return {
                'success': True,
                'message': f'Reagendado na fila de alta prioridade (task: {task.id})',
                'task_id': task.id
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Erro ao reagendar: {str(e)}'}
    
    def _notify_admin(self, phone: str, message: str, media_url: str = None, 
                     error: Exception = None, client_id: int = None) -> Dict[str, Any]:
        """
        Estratégia 3: Notifica administradores sobre a falha
        """
        try:
            # Verifica se já notificou recentemente para evitar spam
            cache_key = f"admin_notification_cooldown_{phone}"
            if cache.get(cache_key):
                return {'success': True, 'message': 'Notificação em cooldown'}
            
            # Prepara dados do cliente
            client_info = "Cliente desconhecido"
            if client_id:
                try:
                    client = AuthClient.objects.get(id=client_id)
                    client_info = f"{client.name} ({client.whatsapp})"
                except AuthClient.DoesNotExist:
                    pass
            
            # Monta email de notificação
            subject = "🚨 FALHA NA EVOLUTION API - Mensagem WhatsApp"
            email_message = f"""
            ALERTA: Falha no envio de mensagem WhatsApp
            
            📱 Cliente: {client_info}
            📞 Telefone: {phone}
            📝 Mensagem: {message[:200]}{'...' if len(message) > 200 else ''}
            📎 Mídia: {media_url or 'Nenhuma'}
            
            ❌ Erro: {str(error) if error else 'Erro desconhecido'}
            🕐 Timestamp: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
            
            AÇÃO NECESSÁRIA: Verificar status da Evolution API e reenviar mensagem manualmente se necessário.
            """
            
            # Lista de emails de administradores (configurar no settings)
            admin_emails = getattr(settings, 'ADMIN_EMAILS', ['admin@example.com'])
            
            send_mail(
                subject=subject,
                message=email_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False
            )
            
            # Define cooldown de 1 hora
            cache.set(cache_key, True, 3600)
            
            logger.info(f"[FALLBACK] Administradores notificados sobre falha para {phone}")
            
            return {
                'success': True,
                'message': f'Administradores notificados por email',
                'admin_count': len(admin_emails)
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Erro ao notificar admin: {str(e)}'}
    
    def _log_for_manual_processing(self, phone: str, message: str, media_url: str = None, 
                                  error: Exception = None, client_id: int = None) -> Dict[str, Any]:
        """
        Estratégia 4: Salva para processamento manual posterior
        """
        try:
            # Salva mensagem como "pendente processamento manual"
            if client_id:
                try:
                    client = AuthClient.objects.get(id=client_id)
                    WhatsAppMessage.objects.create(
                        client=client,
                        content=f"[MANUAL_REQUIRED] {message}",
                        message_type='SENT',
                        direction='SENT',
                        status='manual_required',
                        media_url=media_url
                    )
                    
                    logger.warning(f"[FALLBACK] Mensagem salva para processamento manual: {phone}")
                    
                    return {
                        'success': True,
                        'message': 'Mensagem salva para processamento manual',
                        'requires_manual_action': True
                    }
                    
                except AuthClient.DoesNotExist:
                    pass
            
            # Se não tem cliente, apenas loga
            logger.error(f"[FALLBACK] PROCESSAMENTO MANUAL NECESSÁRIO - {phone}: {message[:100]}")
            
            return {
                'success': True,
                'message': 'Mensagem logada para processamento manual',
                'requires_manual_action': True
            }
            
        except Exception as e:
            return {'success': False, 'message': f'Erro ao salvar para manual: {str(e)}'}
    
    def _save_fallback_log(self, fallback_result: Dict[str, Any], client_id: int = None):
        """Salva log detalhado do fallback no banco"""
        try:
            # Aqui você pode criar uma tabela específica para logs de fallback
            # Por enquanto, vamos usar o log do Django
            logger.info(f"[FALLBACK_LOG] {json.dumps(fallback_result, indent=2)}")
            
        except Exception as e:
            logger.error(f"[FALLBACK] Erro ao salvar log: {str(e)}")
    
    def get_manual_processing_queue(self) -> List[Dict[str, Any]]:
        """
        Retorna mensagens que precisam de processamento manual
        """
        try:
            manual_messages = WhatsAppMessage.objects.filter(
                status='manual_required',
                content__startswith='[MANUAL_REQUIRED]'
            ).order_by('timestamp')
            
            queue = []
            for msg in manual_messages:
                queue.append({
                    'id': msg.id,
                    'client': msg.client.name,
                    'phone': msg.client.whatsapp,
                    'message': msg.content.replace('[MANUAL_REQUIRED] ', ''),
                    'timestamp': msg.timestamp.isoformat(),
                    'media_url': msg.media_url
                })
            
            return queue
            
        except Exception as e:
            logger.error(f"[FALLBACK] Erro ao obter fila manual: {str(e)}")
            return []
    
    def mark_manual_message_processed(self, message_id: int) -> bool:
        """
        Marca mensagem manual como processada
        """
        try:
            msg = WhatsAppMessage.objects.get(id=message_id, status='manual_required')
            msg.status = 'manual_processed'
            msg.save()
            
            logger.info(f"[FALLBACK] Mensagem {message_id} marcada como processada manualmente")
            return True
            
        except WhatsAppMessage.DoesNotExist:
            logger.warning(f"[FALLBACK] Mensagem {message_id} não encontrada para marcar como processada")
            return False
        except Exception as e:
            logger.error(f"[FALLBACK] Erro ao marcar mensagem como processada: {str(e)}")
            return False 