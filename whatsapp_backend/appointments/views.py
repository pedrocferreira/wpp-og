from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from datetime import datetime, timedelta, time
from django.utils import timezone
from django.conf import settings
import json
import logging
import pytz

from .models import Appointment, Client
from whatsapp.models import Message
from whatsapp.evolution_service import EvolutionService
from whatsapp.models import EvolutionConfig

logger = logging.getLogger(__name__)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = None  # Definiremos depois se necessário

@api_view(['GET'])
@permission_classes([AllowAny])
def get_available_time_slots(request):
    """
    Retorna os horários disponíveis para uma data específica
    """
    try:
        date_str = request.GET.get('date')
        consultation_type = request.GET.get('type', 'presencial')
        
        if not date_str:
            return Response({'error': 'Data é obrigatória'}, status=400)
        
        # Converter string para objeto date
        date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        # Verificar se a data não é no passado
        if date < timezone.now().date():
            return Response({'error': 'Não é possível agendar para datas passadas'}, status=400)
        
        # Verificar se não é domingo
        if date.weekday() == 6:  # 6 = domingo
            return Response([], safe=False)
        
        # Horários de funcionamento
        if date.weekday() == 5:  # Sábado
            available_hours = ['08:00', '09:00', '10:00', '11:00', '12:00']
        else:  # Segunda a sexta
            available_hours = [
                '08:00', '09:00', '10:00', '11:00',
                '14:00', '15:00', '16:00', '17:00'
            ]
        
        # Buscar agendamentos já existentes para esta data
        # Converter para timezone local para busca correta
        tz = pytz.timezone('America/Sao_Paulo')
        existing_appointments = Appointment.objects.filter(
            date_time__date=date,
            status__in=['scheduled', 'confirmed']
        ).values_list('date_time', flat=True)
        
        # Converter horários para timezone local para comparação
        existing_appointments_local = [apt.astimezone(tz) for apt in existing_appointments]
        
        # Converter para string para comparação
        existing_times = [apt.strftime('%H:%M') for apt in existing_appointments_local]
        
        # Filtrar horários disponíveis
        available_slots = [hour for hour in available_hours if hour not in existing_times]
        
        return Response(available_slots, status=200)
        
    except Exception as e:
        logger.error(f"Erro ao buscar horários disponíveis: {e}")
        return Response({'error': 'Erro interno do servidor'}, status=500)

@api_view(['POST'])
@permission_classes([AllowAny])
def book_appointment(request):
    """
    Cria um novo agendamento
    """
    try:
        data = request.data
        
        # Validar dados obrigatórios
        required_fields = ['client_name', 'client_whatsapp', 'consultation_type', 'date', 'time']
        for field in required_fields:
            if not data.get(field):
                return Response({'error': f'Campo {field} é obrigatório'}, status=400)
        
        # Processar WhatsApp (remover formatação)
        whatsapp = data['client_whatsapp'].replace('(', '').replace(')', '').replace(' ', '').replace('-', '')
        if not whatsapp.startswith('55'):
            whatsapp = '55' + whatsapp
        
        # Buscar ou criar cliente
        client, created = Client.objects.get_or_create(
            whatsapp=whatsapp,
            defaults={
                'name': data['client_name'],
                'email': data.get('client_email', '')
            }
        )
        
        # Se cliente já existe, atualizar nome se necessário
        if not created and client.name != data['client_name']:
            client.name = data['client_name']
            if data.get('client_email'):
                client.email = data['client_email']
            client.save()
        
        # Criar datetime do agendamento
        date_obj = datetime.strptime(data['date'], '%Y-%m-%d').date()
        time_obj = datetime.strptime(data['time'], '%H:%M').time()
        # Combinar data e hora no timezone local do Brasil
        naive_datetime = datetime.combine(date_obj, time_obj)
        appointment_datetime = timezone.make_aware(
            naive_datetime, timezone=pytz.timezone('America/Sao_Paulo')
        )
        
        # Verificar se horário ainda está disponível
        existing = Appointment.objects.filter(
            date_time=appointment_datetime,
            status__in=['scheduled', 'confirmed']
        ).exists()
        
        if existing:
            return Response({'error': 'Este horário não está mais disponível'}, status=400)
        
        # Tentar integração com Google Calendar
        google_event = None
        try:
            from whatsapp.calendar_service import GoogleCalendarService
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            admin_user = User.objects.filter(is_superuser=True).first()
            
            if admin_user:
                calendar_service = GoogleCalendarService()
                if calendar_service.load_credentials(admin_user):
                    # Cria evento no Google Calendar
                    google_event = calendar_service.create_appointment(
                        client.name,
                        whatsapp,
                        appointment_datetime,
                        appointment_datetime + timedelta(hours=1),
                        f"Consulta {data['consultation_type']} agendada via sistema online"
                    )
                    logger.info(f"Evento criado no Google Calendar: {google_event.get('id') if google_event else 'Erro'}")
                else:
                    logger.warning("Credenciais Google Calendar não carregadas")
            else:
                logger.warning("Usuário admin não encontrado para Google Calendar")
                
        except Exception as e:
            logger.error(f"Erro na integração Google Calendar: {e}")
            # Não falha o agendamento se Google Calendar der erro

        # Criar agendamento no banco local
        appointment = Appointment.objects.create(
            client=client,
            date_time=appointment_datetime,
            google_calendar_event_id=google_event.get('id') if google_event else None,
            status='scheduled',
            source='site',
            description=f"Consulta {data['consultation_type']} agendada via sistema online"
        )
        
        # Criar lembretes automáticos
        try:
            from appointments.models import AppointmentReminder
            
            # Lembrete 1 dia antes
            one_day_before = appointment_datetime - timedelta(days=1)
            if one_day_before.hour < 9:
                one_day_before = one_day_before.replace(hour=9, minute=0, second=0)
            
            if one_day_before > timezone.now():
                AppointmentReminder.objects.get_or_create(
                    appointment=appointment,
                    reminder_type='1_day',
                    defaults={
                        'scheduled_for': one_day_before,
                        'sent': False
                    }
                )
            
            # Lembrete 2 horas antes
            two_hours_before = appointment_datetime - timedelta(hours=2)
            if two_hours_before > timezone.now():
                AppointmentReminder.objects.get_or_create(
                    appointment=appointment,
                    reminder_type='2_hours',
                    defaults={
                        'scheduled_for': two_hours_before,
                        'sent': False
                    }
                )
            
            logger.info(f"Lembretes criados para agendamento {appointment.id}")
            
        except Exception as e:
            logger.error(f"Erro ao criar lembretes: {e}")
            # Não falha o agendamento se criar lembretes der erro
        
        # Enviar confirmação via WhatsApp
        try:
            # Pega a configuração para a instância específica definida nas configurações
            instance_id = settings.EVOLUTION_INSTANCE_ID
            config = EvolutionConfig.objects.filter(instance_id=instance_id).first()

            if not config:
                raise ValueError(f"Nenhuma configuração do Evolution encontrada para a instância '{instance_id}'.")

            evolution_service = EvolutionService()
            # Sobrescreve os headers com a chave de API e token corretos para a instância
            evolution_service.headers['apikey'] = config.api_key
            evolution_service.headers['token'] = config.api_key
            
            consultation_type_label = "Presencial 🏥" if data['consultation_type'] == 'presencial' else "Online 💻"
            
            formatted_date = appointment_datetime.strftime('%d/%m/%Y')
            formatted_time = appointment_datetime.strftime('%H:%M')
            weekday = appointment_datetime.strftime('%A')
            weekday_pt = {
                'Monday': 'Segunda-feira',
                'Tuesday': 'Terça-feira', 
                'Wednesday': 'Quarta-feira',
                'Thursday': 'Quinta-feira',
                'Friday': 'Sexta-feira',
                'Saturday': 'Sábado'
            }.get(weekday, weekday)
            
            confirmation_message = f"""✅ *Agendamento Confirmado!*

Olá {client.name}! 👋

Seu agendamento foi realizado com sucesso:

📅 *Data:* {weekday_pt}, {formatted_date}
⏰ *Horário:* {formatted_time}
🏥 *Tipo:* Consulta {consultation_type_label}

📝 *Importante:*
• Chegue com 15 minutos de antecedência
• Traga documento com foto
• Em caso de imprevisto, entre em contato conosco

Qualquer dúvida, estou aqui para ajudar! 😊

_Agendamento #{appointment.id}_"""

            # Enviar mensagem
            response = evolution_service.send_message(whatsapp, confirmation_message)
            
            # Salvar mensagem no banco
            Message.objects.create(
                client=client,
                content=confirmation_message,
                message_type='text',
                direction='outgoing',
                timestamp=timezone.now(),
                status='sent'
            )
            
            logger.info(f"Confirmação de agendamento enviada para {whatsapp}")
            
        except Exception as e:
            logger.error(f"Erro ao enviar confirmação por WhatsApp: {e}")
            # Não falhar o agendamento se não conseguir enviar WhatsApp
        
        return Response({
            'message': 'Agendamento criado com sucesso',
            'appointment_id': appointment.id,
            'client': client.name,
            'date_time': appointment_datetime.isoformat()
        }, status=201)
        
    except Exception as e:
        logger.error(f"Erro ao criar agendamento: {e}")
        return Response({'error': 'Erro interno do servidor'}, status=500)

@api_view(['GET'])
@permission_classes([AllowAny])
def appointment_success(request):
    """
    Página de sucesso do agendamento (opcional)
    """
    return Response({
        'message': 'Agendamento realizado com sucesso!',
        'instructions': 'Você receberá uma confirmação via WhatsApp em breve.'
    })
