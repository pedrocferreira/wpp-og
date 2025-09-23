from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.conf import settings
from .models import WhatsAppMessage, WebhookLog, AIResponse, Message, Conversation
from appointments.models import Client, Appointment
from .services import EvolutionAPIService
from .test_response import TestAIService
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
import logging
from django.views.decorators.csrf import csrf_exempt
from .evolution_service import EvolutionService
# from .ai_service import AIService, IntentProcessor  # Comentado - usando SmartAIService
import json
from django.utils import timezone

logger = logging.getLogger(__name__)

# Create your views here.

class WebhookView(APIView):
    """
    Endpoint OTIMIZADO para receber webhooks da Evolution API
    Processa de forma assíncrona para evitar timeouts
    Aceita tanto rotas genéricas quanto específicas
    """
    def post(self, request, event_type=None):
        try:
            # Resposta rápida para a Evolution API
            webhook_data = request.data.copy()
            
            # Adiciona o tipo de evento da URL ao webhook_data se fornecido
            if event_type:
                webhook_data['url_event_type'] = event_type
                logger.info(f"[WEBHOOK] Recebido evento específico: {event_type}")
            
            # Agenda processamento assíncrono
            from .tasks import process_webhook_async
            
            task = process_webhook_async.delay(webhook_data)
            
            logger.info(f"[WEBHOOK] Processamento agendado (task: {task.id})")
            
            # Retorna resposta imediata para evitar timeout
            return Response({
                'status': 'received',
                'task_id': task.id,
                'event_type': event_type,
                'message': 'Webhook recebido e agendado para processamento'
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("Erro ao receber webhook: %s", str(e))
            return Response(
                {'error': 'Erro interno do servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ConnectionStatusView(APIView):
    """
    Endpoint para verificar o status da conexão com o WhatsApp
    """
    def get(self, request):
        try:
            evolution_service = EvolutionAPIService()
            status_data = evolution_service.get_connection_status()
            return Response(status_data)
        except Exception as e:
            logger.error("Erro ao verificar status - %s", str(e))
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DisconnectView(APIView):
    """
    Endpoint para desconectar a sessão do WhatsApp
    """
    def post(self, request):
        try:
            evolution_service = EvolutionAPIService()
            result = evolution_service.disconnect()
            return Response(result)
        except Exception as e:
            logger.error("Erro ao desconectar - %s", str(e))
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class WhatsAppMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciar mensagens do WhatsApp
    """
    permission_classes = [IsAuthenticated]
    queryset = WhatsAppMessage.objects.all()
    
    def get_serializer_class(self):
        from .serializers import WhatsAppMessageSerializer
        return WhatsAppMessageSerializer

    def perform_create(self, serializer):
        message = serializer.save()
        
        # Se for uma mensagem de saída, envia via Evolution API
        if message.message_type == 'outgoing':
            evolution_service = EvolutionAPIService()
            evolution_service.send_message(
                message.client.whatsapp,
                message.content,
                message.media_url
            )

    @action(detail=True, methods=['get'])
    def ai_responses(self, request, pk=None):
        from .serializers import AIResponseSerializer
        message = self.get_object()
        responses = AIResponse.objects.filter(message=message)
        serializer = AIResponseSerializer(responses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        total = WhatsAppMessage.objects.count()
        incoming = WhatsAppMessage.objects.filter(message_type='incoming').count()
        outgoing = WhatsAppMessage.objects.filter(message_type='outgoing').count()
        ai_processed = WhatsAppMessage.objects.filter(processed_by_ai=True).count()
        
        return Response({
            'total_messages': total,
            'incoming_messages': incoming,
            'outgoing_messages': outgoing,
            'ai_processed': ai_processed
        })

@api_view(['GET'])
@permission_classes([AllowAny])
def webhook_debug(request):
    """
    Endpoint para debug - mostra informações sobre webhooks
    """
    from django.urls import reverse
    
    webhook_urls = [
        reverse('evolution-webhook'),
        reverse('evolution-webhook-contacts-update'),
        reverse('evolution-webhook-contacts-upsert'),
        reverse('evolution-webhook-messages-upsert'),
        reverse('evolution-webhook-messages-update'),
        reverse('evolution-webhook-qr-update'),
        reverse('evolution-webhook-connection-update'),
    ]
    
    return Response({
        'available_webhook_urls': webhook_urls,
        'base_url': request.build_absolute_uri('/api/whatsapp/'),
        'status': 'webhook endpoints available'
    })

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def evolution_webhook(request):
    """
    Endpoint para receber webhooks do Evolution API
    """
    try:
        # Log do tipo de evento recebido
        event_type = request.data.get('event', 'unknown')
        logger.info("Webhook recebido - Evento: %s", event_type)
        
        # Registra o webhook
        webhook_log = WebhookLog.objects.create(
            payload=request.data
        )

        # Processa apenas eventos de mensagem
        if event_type == 'messages.upsert':
            evolution_service = EvolutionService()
            # Processa a mensagem recebida
            evolution_service.process_webhook(request.data)
        else:
            # Para outros tipos de eventos, apenas registra
            logger.info("Evento %s registrado mas não processado", event_type)

        webhook_log.processed = True
        webhook_log.save()

        return Response({'status': 'processed', 'event': event_type}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error("Erro ao processar webhook: %s", str(e))
        if 'webhook_log' in locals():
            webhook_log.error_message = str(e)
            webhook_log.save()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class MonitoringView(APIView):
    """
    Endpoint para monitoramento do sistema WhatsApp
    """
    permission_classes = [AllowAny]  # Pode ser ajustado conforme necessário
    
    def get(self, request):
        """Retorna status de saúde do sistema"""
        try:
            from .monitoring import WhatsAppMonitor
            
            monitor = WhatsAppMonitor()
            health_data = monitor.get_system_health()
            
            return Response(health_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao obter status de saúde: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AlertsView(APIView):
    """
    Endpoint para alertas do sistema
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Retorna alertas ativos do sistema"""
        try:
            from .monitoring import WhatsAppMonitor
            
            monitor = WhatsAppMonitor()
            alerts = monitor.get_alerts()
            
            return Response({
                'alerts': alerts,
                'count': len(alerts),
                'timestamp': timezone.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao obter alertas: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MetricsView(APIView):
    """
    Endpoint para métricas de performance
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Retorna métricas detalhadas de performance"""
        try:
            from .monitoring import WhatsAppMonitor
            
            monitor = WhatsAppMonitor()
            metrics = monitor.get_performance_metrics()
            
            return Response(metrics, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao obter métricas: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QueueStatsView(APIView):
    """
    Endpoint para estatísticas das filas de mensagens
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """Retorna estatísticas das filas Celery"""
        try:
            from .async_message_service import AsyncMessageService
            
            async_service = AsyncMessageService()
            stats = async_service.get_queue_stats()
            
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas da fila: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RetryFailedMessagesView(APIView):
    """
    Endpoint para reprocessar mensagens falhadas
    """
    permission_classes = [IsAuthenticated]  # Requer autenticação
    
    def post(self, request):
        """Reprocessa mensagens que falharam"""
        try:
            hours = request.data.get('hours', 24)
            
            from .async_message_service import AsyncMessageService
            
            async_service = AsyncMessageService()
            result = async_service.retry_failed_messages(hours=hours)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao reprocessar mensagens: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TaskStatusView(APIView):
    """
    Endpoint para verificar status de tarefas específicas
    """
    permission_classes = [AllowAny]
    
    def get(self, request, task_id):
        """Verifica status de uma tarefa específica"""
        try:
            from .async_message_service import AsyncMessageService
            
            async_service = AsyncMessageService()
            task_status = async_service.get_task_status(task_id)
            
            return Response(task_status, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Erro ao verificar status da tarefa: {str(e)}")
            return Response(
                {'error': 'Erro interno do servidor'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
