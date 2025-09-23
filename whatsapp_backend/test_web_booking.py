#!/usr/bin/env python3
"""
Script para testar agendamento via formulário web
"""
import os
import sys
import django
from datetime import datetime, timedelta
import requests
import json

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from appointments.models import Appointment, Client

def test_web_booking():
    print("🧪 TESTE AGENDAMENTO VIA FORMULÁRIO WEB")
    print("=" * 50)
    
    # Dados de teste
    test_data = {
        'client_name': 'Teste Google Calendar',
        'client_whatsapp': '5511999999999',
        'client_email': 'teste@gmail.com',
        'consultation_type': 'presencial',
        'date': (datetime.now() + timedelta(days=2)).strftime('%Y-%m-%d'),
        'time': '15:00'
    }
    
    print(f"📋 Dados do teste:")
    for key, value in test_data.items():
        print(f"   {key}: {value}")
    
    # Fazer requisição para a API
    try:
        print(f"\n🌐 Fazendo requisição para a API...")
        url = 'http://localhost:8000/api/appointments/book/'
        
        response = requests.post(url, json=test_data, headers={
            'Content-Type': 'application/json'
        })
        
        print(f"Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Agendamento criado com sucesso!")
            print(f"   ID: {data.get('appointment_id')}")
            
            # Verificar no banco se tem Google Calendar ID
            appointment = Appointment.objects.get(id=data.get('appointment_id'))
            print(f"\n📅 Verificação no banco:")
            print(f"   Client: {appointment.client.name}")
            print(f"   Data/Hora: {appointment.date_time}")
            print(f"   Google Calendar ID: {appointment.google_calendar_event_id or 'Não criado'}")
            print(f"   Source: {appointment.source}")
            
            if appointment.google_calendar_event_id:
                print(f"✅ Google Calendar event criado: {appointment.google_calendar_event_id}")
            else:
                print(f"❌ Google Calendar event NÃO foi criado")
            
            # Verificar lembretes
            from appointments.models import AppointmentReminder
            reminders = AppointmentReminder.objects.filter(appointment=appointment)
            print(f"\n🔔 Lembretes criados: {reminders.count()}")
            for reminder in reminders:
                print(f"   - {reminder.get_reminder_type_display()}: {reminder.scheduled_for}")
            
        else:
            print(f"❌ Erro na requisição:")
            print(f"   {response.text}")
            
    except Exception as e:
        print(f"❌ Erro na requisição: {e}")

if __name__ == "__main__":
    test_web_booking() 