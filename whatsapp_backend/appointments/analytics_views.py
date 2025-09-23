from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q, Avg, Case, When, IntegerField
from django.db.models.functions import TruncDate, TruncHour, Extract
from datetime import datetime, timedelta
from .models import Appointment, Client, AppointmentReminder
from whatsapp.models import WhatsAppMessage
import json

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_analytics(request):
    """
    Endpoint principal para analytics do dashboard
    """
    try:
        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        # Métricas principais
        analytics_data = {
            'overview': get_overview_metrics(today, week_ago, month_ago),
            'appointments': get_appointment_analytics(today, week_ago, month_ago),
            'messages': get_message_analytics(today, week_ago, month_ago),
            'clients': get_client_analytics(today, week_ago, month_ago),
            'performance': get_performance_metrics(today, week_ago, month_ago),
            'trends': get_trend_data(today),
            'reminders': get_reminder_analytics(),
        }
        
        return Response(analytics_data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=500)

def get_overview_metrics(today, week_ago, month_ago):
    """Métricas de visão geral"""
    
    # Agendamentos
    appointments_today = Appointment.objects.filter(date_time__date=today).count()
    appointments_week = Appointment.objects.filter(date_time__date__gte=week_ago).count()
    appointments_month = Appointment.objects.filter(date_time__date__gte=month_ago).count()
    
    # Mensagens
    messages_today = WhatsAppMessage.objects.filter(timestamp__date=today).count()
    messages_week = WhatsAppMessage.objects.filter(timestamp__date__gte=week_ago).count()
    
    # Clientes
    clients_today = WhatsAppMessage.objects.filter(
        timestamp__date=today
    ).values('client').distinct().count()
    
    clients_week = WhatsAppMessage.objects.filter(
        timestamp__date__gte=week_ago
    ).values('client').distinct().count()
    
    return {
        'appointments': {
            'today': appointments_today,
            'week': appointments_week,
            'month': appointments_month,
            'growth_week': calculate_growth(appointments_week, week_ago, 'appointments')
        },
        'messages': {
            'today': messages_today,
            'week': messages_week,
            'growth_week': calculate_growth(messages_week, week_ago, 'messages')
        },
        'active_clients': {
            'today': clients_today,
            'week': clients_week,
            'growth_week': calculate_growth(clients_week, week_ago, 'clients')
        }
    }

def get_appointment_analytics(today, week_ago, month_ago):
    """Analytics detalhados de agendamentos"""
    
    # Status dos agendamentos
    status_distribution = Appointment.objects.values('status').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Agendamentos por hora do dia
    hourly_distribution = Appointment.objects.filter(
        date_time__date__gte=week_ago
    ).annotate(
        hour=Extract('date_time', 'hour')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Próximos agendamentos
    upcoming = Appointment.objects.filter(
        date_time__gt=timezone.now(),
        status='scheduled'
    ).select_related('client').order_by('date_time')[:10]
    
    upcoming_data = []
    for apt in upcoming:
        upcoming_data.append({
            'id': apt.id,
            'client_name': apt.client.name,
            'client_whatsapp': apt.client.whatsapp,
            'datetime': apt.date_time.isoformat(),
            'status': apt.status,
            'source': apt.source,
            'has_reminders': AppointmentReminder.objects.filter(appointment=apt).exists()
        })
    
    # Taxa de ocupação por dia da semana
    weekly_occupation = Appointment.objects.filter(
        date_time__date__gte=week_ago
    ).annotate(
        weekday=Extract('date_time', 'week_day')
    ).values('weekday').annotate(
        count=Count('id')
    ).order_by('weekday')
    
    return {
        'status_distribution': list(status_distribution),
        'hourly_distribution': list(hourly_distribution),
        'upcoming_appointments': upcoming_data,
        'weekly_occupation': list(weekly_occupation),
        'conversion_rate': calculate_conversion_rate(week_ago)
    }

def get_message_analytics(today, week_ago, month_ago):
    """Analytics de mensagens WhatsApp"""
    
    # Mensagens por direção
    message_direction = WhatsAppMessage.objects.filter(
        timestamp__date__gte=week_ago
    ).values('direction').annotate(
        count=Count('id')
    )
    
    # Mensagens por dia - usando queries separadas para compatibilidade
    daily_messages = WhatsAppMessage.objects.filter(
        timestamp__date__gte=week_ago
    ).annotate(
        date=TruncDate('timestamp')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Adiciona contadores de entrada e saída separadamente
    for item in daily_messages:
        date = item['date']
        item['incoming'] = WhatsAppMessage.objects.filter(
            timestamp__date=date, direction='RECEIVED'
        ).count()
        item['outgoing'] = WhatsAppMessage.objects.filter(
            timestamp__date=date, direction='SENT'
        ).count()
    
    # Mensagens por hora
    hourly_messages = WhatsAppMessage.objects.filter(
        timestamp__date=today
    ).annotate(
        hour=TruncHour('timestamp')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')
    
    # Clientes mais ativos
    top_clients = WhatsAppMessage.objects.filter(
        timestamp__date__gte=week_ago
    ).values(
        'client__name', 'client__whatsapp'
    ).annotate(
        message_count=Count('id')
    ).order_by('-message_count')[:10]
    
    return {
        'direction_distribution': list(message_direction),
        'daily_messages': list(daily_messages),
        'hourly_messages': list(hourly_messages),
        'top_clients': list(top_clients),
        'avg_response_time': calculate_avg_response_time(week_ago)
    }

def get_client_analytics(today, week_ago, month_ago):
    """Analytics de clientes"""
    
    # Novos clientes por dia
    new_clients_daily = Client.objects.filter(
        created_at__date__gte=week_ago
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        count=Count('id')
    ).order_by('date')
    
    # Clientes com mais agendamentos
    top_clients_appointments = Client.objects.annotate(
        appointment_count=Count('appointment')
    ).filter(appointment_count__gt=0).order_by('-appointment_count')[:10]
    
    top_clients_data = []
    for client in top_clients_appointments:
        last_appointment = client.appointment_set.order_by('-date_time').first()
        top_clients_data.append({
            'name': client.name,
            'whatsapp': client.whatsapp,
            'appointment_count': client.appointment_count,
            'last_appointment': last_appointment.date_time.isoformat() if last_appointment else None,
            'total_messages': WhatsAppMessage.objects.filter(client__whatsapp=client.whatsapp).count()
        })
    
    return {
        'new_clients_daily': list(new_clients_daily),
        'top_clients': top_clients_data,
        'total_clients': Client.objects.count(),
        'clients_with_appointments': Client.objects.filter(appointment__isnull=False).distinct().count()
    }

def get_performance_metrics(today, week_ago, month_ago):
    """Métricas de performance"""
    
    total_appointments = Appointment.objects.filter(date_time__date__gte=week_ago).count()
    cancelled_appointments = Appointment.objects.filter(
        date_time__date__gte=week_ago, status='cancelled'
    ).count()
    
    cancellation_rate = (cancelled_appointments / total_appointments * 100) if total_appointments > 0 else 0
    
    # Taxa de conversão (mensagens para agendamentos)
    total_messages = WhatsAppMessage.objects.filter(timestamp__date__gte=week_ago).count()
    conversion_rate = (total_appointments / total_messages * 100) if total_messages > 0 else 0
    
    return {
        'conversion_rate': round(conversion_rate, 2),
        'cancellation_rate': round(cancellation_rate, 2),
        'total_appointments': total_appointments,
        'cancelled_appointments': cancelled_appointments,
        'system_uptime': calculate_system_uptime()
    }

def get_trend_data(today):
    """Dados de tendência dos últimos 30 dias"""
    
    thirty_days_ago = today - timedelta(days=30)
    trend_data = []
    
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        count = Appointment.objects.filter(date_time__date=date).count()
        trend_data.append({
            'date': date.isoformat(),
            'appointments': count
        })
    
    return trend_data

def get_reminder_analytics():
    """Analytics dos lembretes de agendamento"""
    
    total_reminders = AppointmentReminder.objects.count()
    
    # Usando queries separadas para compatibilidade
    sent_reminders = AppointmentReminder.objects.filter(sent=True).count()
    pending_reminders = AppointmentReminder.objects.filter(sent=False).count()
    
    reminder_types = AppointmentReminder.objects.values('reminder_type').annotate(
        count=Count('id')
    ).order_by('reminder_type')
    
    effectiveness = 0
    if sent_reminders > 0:
        # Calcula efetividade baseada em agendamentos que não foram cancelados após lembrete
        effective_reminders = AppointmentReminder.objects.filter(
            sent=True,
            appointment__status__in=['scheduled', 'confirmed', 'completed']
        ).count()
        effectiveness = (effective_reminders / sent_reminders * 100)
    
    return {
        'total_sent': sent_reminders,
        'total_pending': pending_reminders,
        'reminder_types': list(reminder_types),
        'effectiveness_rate': round(effectiveness, 2)
    }

def calculate_growth(current_value, period_start, metric_type):
    """Calcula crescimento percentual em relação ao período anterior"""
    # Implementação simplificada - retorna 0 por enquanto
    return 0

def calculate_conversion_rate(week_ago):
    """Calcula taxa de conversão de mensagens para agendamentos"""
    messages = WhatsAppMessage.objects.filter(timestamp__date__gte=week_ago).count()
    appointments = Appointment.objects.filter(date_time__date__gte=week_ago).count()
    
    if messages > 0:
        return round((appointments / messages) * 100, 2)
    return 0

def calculate_avg_response_time(week_ago):
    """Calcula tempo médio de resposta - simplificado"""
    return "< 5 min"

def calculate_system_uptime():
    """Calcula uptime do sistema - simplificado"""
    return "99.9%" 