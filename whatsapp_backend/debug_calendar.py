#!/usr/bin/env python3
"""
Script de diagnóstico para integração Google Calendar
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from authentication.models import User
from core.models import GoogleCalendarCredentials
from whatsapp.calendar_service import GoogleCalendarService
from appointments.models import Client, Appointment
import pytz

def test_google_calendar():
    print("🔍 DIAGNÓSTICO GOOGLE CALENDAR")
    print("=" * 50)
    
    # 1. Verificar usuários admin
    admin_users = User.objects.filter(is_superuser=True)
    print(f"👤 Usuários admin: {admin_users.count()}")
    for user in admin_users:
        print(f"   - {user.username} (ID: {user.id})")
    
    # 2. Verificar credenciais
    credentials = GoogleCalendarCredentials.objects.all()
    print(f"\n🔑 Credenciais Google: {credentials.count()}")
    for cred in credentials:
        print(f"   - User: {cred.user.username}")
        print(f"   - Ativa: {cred.is_active}")
        print(f"   - Expiry: {cred.expiry}")
        print(f"   - Client ID: {cred.client_id[:20]}...")
    
    # 3. Testar serviço
    print(f"\n🧪 TESTE DO SERVIÇO")
    admin_user = admin_users.first()
    if not admin_user:
        print("❌ Nenhum usuário admin encontrado!")
        return
    
    service = GoogleCalendarService()
    print(f"Testando com usuário: {admin_user.username}")
    
    # Carregar credenciais
    loaded = service.load_credentials(admin_user)
    print(f"Credenciais carregadas: {'✅' if loaded else '❌'}")
    
    if not loaded:
        print("❌ Não foi possível carregar credenciais!")
        return
    
    print(f"Serviço inicializado: {'✅' if service.service else '❌'}")
    
    # 4. Testar criação de evento
    print(f"\n📅 TESTE CRIAÇÃO DE EVENTO")
    try:
        now = datetime.now(pytz.timezone('America/Sao_Paulo'))
        start_time = now + timedelta(hours=1)
        end_time = start_time + timedelta(hours=1)
        
        print(f"Criando evento de teste...")
        print(f"Início: {start_time}")
        print(f"Fim: {end_time}")
        
        event = service.create_appointment(
            client_name="Cliente Teste DEBUG",
            client_phone="5511999999999",
            start_datetime=start_time,
            end_datetime=end_time,
            description="Evento de teste criado pelo diagnóstico"
        )
        
        if event:
            print(f"✅ Evento criado com sucesso!")
            print(f"   ID: {event.get('id')}")
            print(f"   Link: {event.get('htmlLink')}")
            
            # Tentar deletar o evento de teste
            try:
                service.cancel_appointment(event.get('id'))
                print(f"✅ Evento de teste removido")
            except Exception as e:
                print(f"⚠️  Erro ao remover evento de teste: {e}")
        else:
            print(f"❌ Falha ao criar evento!")
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. Verificar agendamentos existentes
    print(f"\n📋 AGENDAMENTOS NO BANCO")
    appointments = Appointment.objects.filter(
        date_time__gte=datetime.now() - timedelta(days=7)
    ).order_by('-date_time')[:5]
    
    print(f"Últimos {appointments.count()} agendamentos:")
    for apt in appointments:
        has_google_id = bool(apt.google_calendar_event_id)
        print(f"   - {apt.client.name} | {apt.date_time.strftime('%d/%m %H:%M')} | Google: {'✅' if has_google_id else '❌'}")
        if has_google_id:
            print(f"     Event ID: {apt.google_calendar_event_id}")

if __name__ == "__main__":
    test_google_calendar() 