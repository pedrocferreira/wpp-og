from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from django.conf import settings
from .models import WhatsAppMessage, WebhookLog, AIResponse
from appointments.models import Client
from .services import EvolutionAPIService
from .test_response import TestAIService
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
import logging
from django.views.decorators.csrf import csrf_exempt
from .evolution_service import EvolutionService

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
            
            webhook_data = evolution_service.process_webhook(request.data)
            
            if not webhook_data:
                return Response({'status': 'ignored'}, status=status.HTTP_200_OK)

            # Busca ou cria o cliente
            client, created = Client.objects.get_or_create(
                whatsapp=webhook_data['whatsapp_number'],
                defaults={'name': f"Cliente {webhook_data['whatsapp_number']}"}
            )

            # Cria a mensagem
            message = WhatsAppMessage.objects.create(
                client=client,
                message_type='incoming',
                content=webhook_data['content'],
                status='received'
            )

            # Processa com IA
            ai_response = ai_service.process_message(
                webhook_data['content'],
                context={'client_name': client.name}
            )

            # Salva a resposta da IA
            AIResponse.objects.create(
                message=message,
                response_text=ai_response['response_text'],
                confidence_score=ai_response['confidence_score'],
                intent_detected=ai_response['intent_detected']
            )

            # Envia resposta via WhatsApp
            evolution_service.send_message(
                client.whatsapp,
                ai_response['response_text']
            )

            webhook_log.processed = True
            webhook_log.save()

            return Response({'status': 'processed'}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Erro ao processar webhook: {str(e)}")
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
            logger.error(f"Erro ao verificar status: {str(e)}")
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
            logger.error(f"Erro ao desconectar: {str(e)}")
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
        logger.info("Webhook recebido: %s", request.data)
        
        # Registra o webhook
        webhook_log = WebhookLog.objects.create(
            payload=request.data
        )

        # Processa o webhook
        evolution_service = EvolutionService()
        ai_service = TestAIService()
        
        # Processa a mensagem recebida
        whatsapp_message = evolution_service.process_webhook(request.data)
        
        if whatsapp_message:
            logger.info(f"Mensagem processada: {whatsapp_message}")
            
            # Processa com IA
            ai_response = ai_service.process_message(
                whatsapp_message.content,
                context={'client_name': whatsapp_message.client.name}
            )

            # Salva a resposta da IA
            AIResponse.objects.create(
                message=whatsapp_message,
                response_text=ai_response['response_text'],
                confidence_score=ai_response['confidence_score'],
                intent_detected=ai_response['intent_detected']
            )

            # Envia resposta via WhatsApp
            evolution_service.send_message(
                whatsapp_message.client.whatsapp,
                ai_response['response_text']
            )

            webhook_log.processed = True
            webhook_log.save()
            
            return Response({'status': 'processed'}, status=status.HTTP_200_OK)
        
        return Response({'status': 'ignored'}, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Erro ao processar webhook: {str(e)}")
        if 'webhook_log' in locals():
            webhook_log.error_message = str(e)
            webhook_log.save()
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
