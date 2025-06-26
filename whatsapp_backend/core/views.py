from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone

User = get_user_model()
from whatsapp.calendar_service import GoogleCalendarService
from .models import AISettings
import json
import logging

logger = logging.getLogger(__name__)

@csrf_exempt
@require_http_methods(["GET"])
def google_calendar_auth_url(request):
    """Gera URL de autenticação para Google Calendar"""
    try:
        calendar_service = GoogleCalendarService()
        auth_url = calendar_service.get_auth_url()
        
        if auth_url:
            return JsonResponse({
                'success': True,
                'auth_url': auth_url,
                'message': 'URL de autenticação gerada com sucesso'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao gerar URL de autenticação'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Erro ao gerar URL de autenticação: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def google_calendar_callback(request):
    """Processa callback do Google OAuth e salva credenciais"""
    try:
        data = json.loads(request.body)
        code = data.get('code')
        user_id = data.get('user_id', 1)  # Por padrão usa admin
        
        if not code:
            return JsonResponse({
                'success': False,
                'message': 'Código de autorização não fornecido'
            }, status=400)
        
        # Busca o usuário
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuário não encontrado'
            }, status=404)
        
        # Troca código por credenciais
        calendar_service = GoogleCalendarService()
        success = calendar_service.exchange_code_for_credentials(code, user)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Google Calendar conectado com sucesso!',
                'user': user.username
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao trocar código por credenciais'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Erro no callback Google: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def google_calendar_status(request):
    """Verifica status da conexão com Google Calendar"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuário não encontrado'
            }, status=404)
        
        calendar_service = GoogleCalendarService()
        status = calendar_service.get_connection_status(user)
        
        return JsonResponse({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        logger.error(f"Erro ao verificar status: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def google_calendar_disconnect(request):
    """Desconecta Google Calendar"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id', 1)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuário não encontrado'
            }, status=404)
        
        calendar_service = GoogleCalendarService()
        success = calendar_service.disconnect(user)
        
        if success:
            return JsonResponse({
                'success': True,
                'message': 'Google Calendar desconectado com sucesso'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Erro ao desconectar Google Calendar'
            }, status=500)
            
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Erro ao desconectar: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def google_calendar_test(request):
    """Testa a conexão com Google Calendar"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuário não encontrado'
            }, status=404)
        
        calendar_service = GoogleCalendarService()
        
        # Tenta carregar credenciais e fazer uma requisição de teste
        if calendar_service.load_credentials(user):
            # Busca calendários como teste
            calendars = calendar_service.service.calendarList().list().execute()
            calendar_list = [
                {
                    'id': cal['id'],
                    'summary': cal.get('summary', 'Sem nome'),
                    'primary': cal.get('primary', False)
                }
                for cal in calendars.get('items', [])
            ]
            
            return JsonResponse({
                'success': True,
                'message': 'Conexão com Google Calendar OK',
                'calendars': calendar_list
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Não foi possível conectar ao Google Calendar'
            }, status=500)
            
    except Exception as e:
        logger.error(f"Erro no teste Google Calendar: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["GET"])
def google_calendar_events(request):
    """Busca eventos do Google Calendar"""
    try:
        user_id = request.GET.get('user_id', 1)
        start_date = request.GET.get('start_date')  # formato: 2025-06-24
        end_date = request.GET.get('end_date')    # formato: 2025-06-30
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuário não encontrado'
            }, status=404)
        
        calendar_service = GoogleCalendarService()
        
        if calendar_service.load_credentials(user):
            try:
                # Se não especificar datas, busca próximos 30 dias
                if not start_date:
                    from datetime import datetime, timedelta
                    start_date = datetime.now().strftime('%Y-%m-%d')
                    end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                
                # Adiciona time zone para as datas
                time_min = f"{start_date}T00:00:00Z"
                time_max = f"{end_date}T23:59:59Z"
                
                # Busca eventos do Google Calendar
                events_result = calendar_service.service.events().list(
                    calendarId='primary',
                    timeMin=time_min,
                    timeMax=time_max,
                    singleEvents=True,
                    orderBy='startTime',
                    maxResults=50
                ).execute()
                
                events = events_result.get('items', [])
                
                # Formata eventos para o frontend
                formatted_events = []
                for event in events:
                    start = event['start'].get('dateTime', event['start'].get('date'))
                    end = event['end'].get('dateTime', event['end'].get('date'))
                    
                    formatted_events.append({
                        'id': event['id'],
                        'title': event.get('summary', 'Sem título'),
                        'description': event.get('description', ''),
                        'start': start,
                        'end': end,
                        'location': event.get('location', ''),
                        'status': event.get('status', 'confirmed'),
                        'attendees': [
                            {
                                'email': attendee.get('email', ''),
                                'name': attendee.get('displayName', ''),
                                'responseStatus': attendee.get('responseStatus', '')
                            }
                            for attendee in event.get('attendees', [])
                        ],
                        'created': event.get('created', ''),
                        'updated': event.get('updated', ''),
                        'htmlLink': event.get('htmlLink', ''),
                        'colorId': event.get('colorId', '1')
                    })
                
                return JsonResponse({
                    'success': True,
                    'events': formatted_events,
                    'total': len(formatted_events),
                    'calendar_id': 'primary'
                })
                
            except Exception as e:
                logger.error(f"Erro ao buscar eventos do Google: {e}")
                return JsonResponse({
                    'success': False,
                    'message': f'Erro ao buscar eventos: {str(e)}'
                }, status=500)
        else:
            return JsonResponse({
                'success': False,
                'message': 'Google Calendar não conectado'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Erro ao buscar eventos: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }, status=500)

# ===== AI SETTINGS VIEWS =====

@csrf_exempt
@require_http_methods(["GET"])
def ai_settings_get(request):
    """Busca configurações da IA do usuário"""
    try:
        user_id = request.GET.get('user_id', 1)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuário não encontrado'
            }, status=404)
        
        # Busca ou cria configurações da IA
        ai_settings, created = AISettings.objects.get_or_create(
            user=user,
            defaults={
                'assistant_name': 'Elô',
                'personality': 'Sou uma assistente calorosa, empática e profissional. Sempre procuro ajudar os clientes da melhor forma possível.',
                'clinic_info': 'Clínica especializada em saúde mental e bem-estar, oferecendo atendimento humanizado e personalizado.',
                'doctor_name': 'Dra. Elisa Munaretti',
                'doctor_specialties': ['psicologia'],
                'working_hours': 'Segunda a sexta: 8h às 18h, Sábado: 8h às 13h',
                'appointment_duration': 60,
                'response_style': 'empathetic',
                'use_emojis': True,
                'auto_scheduling': True
            }
        )
        
        return JsonResponse({
            'success': True,
            'settings': {
                'assistant_name': ai_settings.assistant_name,
                'personality': ai_settings.personality,
                'clinic_info': ai_settings.clinic_info,
                'doctor_name': ai_settings.doctor_name,
                'doctor_specialties': ai_settings.doctor_specialties,
                'working_hours': ai_settings.working_hours,
                'appointment_duration': ai_settings.appointment_duration,
                'response_style': ai_settings.response_style,
                'use_emojis': ai_settings.use_emojis,
                'auto_scheduling': ai_settings.auto_scheduling,
                'updated_at': ai_settings.updated_at.isoformat() if ai_settings.updated_at else None
            },
            'created': created
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar configurações da IA: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def ai_settings_save(request):
    """Salva configurações da IA do usuário"""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id', 1)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Usuário não encontrado'
            }, status=404)
        
        # Busca ou cria configurações da IA
        ai_settings, created = AISettings.objects.get_or_create(user=user)
        
        # Atualiza campos se fornecidos
        if 'assistant_name' in data:
            ai_settings.assistant_name = data['assistant_name']
        if 'personality' in data:
            ai_settings.personality = data['personality']
        if 'clinic_info' in data:
            ai_settings.clinic_info = data['clinic_info']
        if 'doctor_name' in data:
            ai_settings.doctor_name = data['doctor_name']
        if 'doctor_specialties' in data:
            ai_settings.doctor_specialties = data['doctor_specialties']
        if 'working_hours' in data:
            ai_settings.working_hours = data['working_hours']
        if 'appointment_duration' in data:
            ai_settings.appointment_duration = data['appointment_duration']
        if 'response_style' in data:
            ai_settings.response_style = data['response_style']
        if 'use_emojis' in data:
            ai_settings.use_emojis = data['use_emojis']
        if 'auto_scheduling' in data:
            ai_settings.auto_scheduling = data['auto_scheduling']
        
        ai_settings.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Configurações da IA salvas com sucesso!',
            'settings': {
                'assistant_name': ai_settings.assistant_name,
                'personality': ai_settings.personality,
                'clinic_info': ai_settings.clinic_info,
                'doctor_name': ai_settings.doctor_name,
                'doctor_specialties': ai_settings.doctor_specialties,
                'working_hours': ai_settings.working_hours,
                'appointment_duration': ai_settings.appointment_duration,
                'response_style': ai_settings.response_style,
                'use_emojis': ai_settings.use_emojis,
                'auto_scheduling': ai_settings.auto_scheduling,
                'updated_at': ai_settings.updated_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'JSON inválido'
        }, status=400)
    except Exception as e:
        logger.error(f"Erro ao salvar configurações da IA: {e}")
        return JsonResponse({
            'success': False,
            'message': f'Erro interno: {str(e)}'
        }, status=500)

@api_view(['GET'])
def system_stats(request):
    """Retorna estatísticas do sistema em tempo real"""
    try:
        from appointments.models import Appointment
        from whatsapp.models import WhatsAppMessage
        from authentication.models import Client as AuthClient
        from django.db.models import Count, Q
        from datetime import datetime, timedelta
        
        # Data de hoje
        today = timezone.now().date()
        this_week = today - timedelta(days=today.weekday())
        this_month = today.replace(day=1)
        
        # Estatísticas de agendamentos
        appointments_today = Appointment.objects.filter(
            date_time__date=today
        ).count()
        
        appointments_this_week = Appointment.objects.filter(
            date_time__date__gte=this_week
        ).count()
        
        appointments_this_month = Appointment.objects.filter(
            date_time__date__gte=this_month
        ).count()
        
        total_appointments = Appointment.objects.count()
        
        # Estatísticas de mensagens
        messages_today = WhatsAppMessage.objects.filter(
            timestamp__date=today
        ).count()
        
        messages_this_week = WhatsAppMessage.objects.filter(
            timestamp__date__gte=this_week
        ).count()
        
        # Mensagens por direção
        incoming_today = WhatsAppMessage.objects.filter(
            timestamp__date=today,
            direction='incoming'
        ).count()
        
        outgoing_today = WhatsAppMessage.objects.filter(
            timestamp__date=today,
            direction='outgoing'
        ).count()
        
        # Clientes únicos
        unique_clients_today = WhatsAppMessage.objects.filter(
            timestamp__date=today
        ).values('client').distinct().count()
        
        unique_clients_week = WhatsAppMessage.objects.filter(
            timestamp__date__gte=this_week
        ).values('client').distinct().count()
        
        # Agendamentos por origem
        whatsapp_appointments = Appointment.objects.filter(
            source='whatsapp'
        ).count()
        
        manual_appointments = Appointment.objects.filter(
            source='manual'
        ).count()
        
        # Taxa de conversão (mensagens -> agendamentos)
        conversion_rate = 0
        if messages_this_week > 0:
            conversion_rate = round((appointments_this_week / messages_this_week) * 100, 2)
        
        # Próximos agendamentos
        upcoming_appointments = Appointment.objects.filter(
            date_time__gte=timezone.now()
        ).order_by('date_time')[:5]
        
        upcoming_list = []
        for apt in upcoming_appointments:
            upcoming_list.append({
                'id': apt.id,
                'client_name': apt.client.name if apt.client else 'Cliente não informado',
                'datetime': apt.date_time.strftime('%d/%m/%Y %H:%M'),
                'source': apt.source,
                'has_google_event': bool(apt.google_calendar_event_id)
            })
        
        # Status Google Calendar
        google_calendar_connected = False
        google_calendar_email = None
        try:
            from core.models import GoogleCalendarCredentials
            credentials = GoogleCalendarCredentials.objects.first()
            if credentials and credentials.access_token:
                google_calendar_connected = True
                google_calendar_email = credentials.email
        except:
            pass
        
        # Status IA
        ai_status = "Ativo"
        ai_settings = None
        try:
            from core.models import AISettings
            ai_settings_obj = AISettings.objects.first()
            if ai_settings_obj:
                ai_settings = {
                    'assistant_name': ai_settings_obj.assistant_name,
                    'personality': ai_settings_obj.personality,
                    'response_style': ai_settings_obj.response_style,
                    'auto_booking_enabled': ai_settings_obj.auto_booking_enabled
                }
        except:
            ai_status = "Erro na configuração"
        
        stats = {
            'appointments': {
                'today': appointments_today,
                'this_week': appointments_this_week,
                'this_month': appointments_this_month,
                'total': total_appointments,
                'by_source': {
                    'whatsapp': whatsapp_appointments,
                    'manual': manual_appointments
                },
                'upcoming': upcoming_list
            },
            'messages': {
                'today': messages_today,
                'this_week': messages_this_week,
                'incoming_today': incoming_today,
                'outgoing_today': outgoing_today
            },
            'clients': {
                'unique_today': unique_clients_today,
                'unique_week': unique_clients_week
            },
            'performance': {
                'conversion_rate': conversion_rate,
                'ai_status': ai_status,
                'ai_settings': ai_settings
            },
            'integrations': {
                'google_calendar': {
                    'connected': google_calendar_connected,
                    'email': google_calendar_email
                }
            },
            'system': {
                'timestamp': timezone.now().isoformat(),
                'timezone': 'America/Sao_Paulo'
            }
        }
        
        return Response({
            'success': True,
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"Erro ao gerar estatísticas: {e}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=500)
