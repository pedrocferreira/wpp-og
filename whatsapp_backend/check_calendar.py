#!/usr/bin/env python3
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from whatsapp.calendar_service import GoogleCalendarService
from django.contrib.auth import get_user_model
from appointments.models import Appointment

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

if not admin_user:
    print("❌ Usuário admin não encontrado!")
    sys.exit(1)

print(f"👤 Usuário admin: {admin_user.email}")

calendar = GoogleCalendarService()
if not calendar.load_credentials(admin_user):
    print("❌ Não foi possível carregar credenciais do Google Calendar")
    sys.exit(1)

print("✅ Credenciais carregadas com sucesso!")

# Listar calendários
try:
    calendar_list = calendar.service.calendarList().list().execute()
    print("\n📅 Calendários disponíveis:")
    for calendar_item in calendar_list['items']:
        primary = "⭐ PRIMARY" if calendar_item.get('primary', False) else ""
        print(f"  - {calendar_item['summary']} (ID: {calendar_item['id']}) {primary}")
except Exception as e:
    print(f"❌ Erro ao listar calendários: {e}")

# Verificar último agendamento
print("\n📋 Último agendamento:")
last_apt = Appointment.objects.last()
if last_apt:
    print(f"  - ID: {last_apt.id}")
    print(f"  - Cliente: {last_apt.client.name}")
    print(f"  - Data: {last_apt.date_time}")
    print(f"  - Status: {last_apt.status}")
    print(f"  - Google Calendar ID: {last_apt.google_calendar_event_id}")
    
    if last_apt.google_calendar_event_id:
        try:
            event = calendar.service.events().get(
                calendarId='primary', 
                eventId=last_apt.google_calendar_event_id
            ).execute()
            print(f"  - Evento no Google: {event.get('summary')}")
            print(f"  - Data/Hora: {event.get('start', {}).get('dateTime')}")
            print(f"  - Calendário: {event.get('organizer', {}).get('email', 'N/A')}")
        except Exception as e:
            print(f"  - ❌ Erro ao buscar evento: {e}")
else:
    print("  - Nenhum agendamento encontrado") 