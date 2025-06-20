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
from .ai_service import AIService, IntentProcessor
import json

logger = logging.getLogger(__name__)

# Create your views here.

class WebhookView(APIView):
    """
    Endpoint para receber webhooks da Evolution API
    """
    def post(self, request):
        try:
            # Registra o webhook
            webhook_log = WebhookLog.objects.create(
                payload=request.data
            )

            # Processa o webhook
            evolution_service = EvolutionAPIService()
            ai_service = TestAIService()
            
            data = request.data
            if data.get('type') == 'message':
                message_data = data.get('message', {})
                if message_data.get('fromMe'):
                    return Response(status=200)
                
                conversation = Conversation.objects.get_or_create(
                    whatsapp_id=message_data.get('from')
                )[0]
                
                # Salva a mensagem recebida
                received_message = Message.objects.create(
                    conversation=conversation,
                    content=message_data.get('body'),
                    is_from_bot=False
                )
                
                # Processa com IA
                ai_service = AIService()
                conversation_history = Message.objects.filter(
                    conversation=conversation
                ).order_by('-created_at')[:5]
                
                response = ai_service.process_message(
                    message_data.get('body'),
                    context={'conversation_history': conversation_history}
                )
                
                # Identifica a intenção
                intent = IntentProcessor.identify_intent(message_data.get('body'))
                
                # Se for agendamento, processa especialmente
                if intent == 'agendamento':
                    # Aqui você pode adicionar lógica específica para agendamento
                    # Por exemplo, criar um Appointment ou iniciar um fluxo de coleta de dados
                    pass
                
                # Salva e envia a resposta
                bot_message = Message.objects.create(
                    conversation=conversation,
                    content=response,
                    is_from_bot=True
                )
                
                # Envia resposta via Evolution API
                evolution_service.send_message(
                    message_data.get('from'),
                    response
                )
            
            webhook_log.processed = True
            webhook_log.save()

            return Response({'status': 'processed'}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error("Erro ao processar webhook - %s", str(e))
            if 'webhook_log' in locals():
                webhook_log.error_message = str(e)
                webhook_log.save()
            return Response(
                {'error': str(e)},
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

@api_view(['POST'])
@csrf_exempt
@permission_classes([AllowAny])
def evolution_webhook(request):
    """
    Endpoint para receber webhooks do Evolution API
    """
    try:
        # Log usando json.dumps para objetos complexos
        logger.info("Webhook recebido: %s", json.dumps(request.data))
        
        # Registra o webhook
        webhook_log = WebhookLog.objects.create(
            payload=request.data
        )

        # Processa o webhook
        evolution_service = EvolutionService()
        
        # Processa a mensagem recebida
        evolution_service.process_webhook(request.data)
        
        webhook_log.processed = True
        webhook_log.save()

        return Response({'status': 'processed'}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error("Erro ao processar webhook: %s", str(e))
        if 'webhook_log' in locals():
            webhook_log.error_message = str(e)
            webhook_log.save()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
