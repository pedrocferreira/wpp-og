#!/usr/bin/env python3
"""
Script para testar a persistência do contexto conversacional
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from authentication.models import Client as AuthClient
from whatsapp.models import WhatsAppMessage
from whatsapp.smart_ai_service import SmartAIService
import pytz

def create_test_messages():
    """Cria mensagens de teste para simular conversa entre dias"""
    print("🧪 CRIANDO MENSAGENS DE TESTE")
    print("=" * 50)
    
    # Busca ou cria cliente de teste
    test_whatsapp = "5511999999999"
    auth_client, created = AuthClient.objects.get_or_create(
        whatsapp=test_whatsapp,
        defaults={
            'name': 'Cliente Teste Contexto',
            'email': 'teste@contexto.com'
        }
    )
    
    if created:
        print(f"✅ Cliente criado: {auth_client.name}")
    else:
        print(f"📱 Cliente existente: {auth_client.name}")
    
    # Remove mensagens antigas de teste
    WhatsAppMessage.objects.filter(client=auth_client).delete()
    
    # Define horários: ontem e hoje
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    tz = pytz.timezone('America/Sao_Paulo')
    
    # Mensagens de ONTEM
    yesterday_morning = yesterday.replace(hour=10, minute=0, second=0)
    yesterday_messages = [
        ("RECEIVED", "Oi! Bom dia"),
        ("SENT", "Oi! Tudo bom? Eu sou a Elô! 😊"),
        ("RECEIVED", "Quero agendar uma consulta"),
        ("SENT", "Claro! Que dia e horário você prefere?"),
        ("RECEIVED", "amanha as 15h tem?"),
        ("SENT", "Deixa eu verificar... Sim! O horário das 15:00 amanhã está livre! 😊\n\nQuer que eu agende pra você?"),
        ("RECEIVED", "sim pode agendar"),
        ("SENT", "Perfeito! Consulta agendada para hoje às 15:00! 🎉")
    ]
    
    for i, (direction, content) in enumerate(yesterday_messages):
        timestamp = yesterday_morning + timedelta(minutes=i*5)
        WhatsAppMessage.objects.create(
            client=auth_client,
            content=content,
            message_type=direction,
            direction=direction,
            timestamp=tz.localize(timestamp),
            message_id=f"test_yesterday_{i}"
        )
    
    # Mensagens de HOJE
    today_morning = today.replace(hour=9, minute=0, second=0)
    today_messages = [
        ("RECEIVED", "Oi de novo!"),
        ("SENT", "Oi! Tudo bom? Vi que você tem consulta hoje às 15:00! 😊"),
        ("RECEIVED", "queria remarcar pra amanha as 16h"),
        ("SENT", "Claro! Deixa eu verificar se amanhã às 16h está livre...")
    ]
    
    for i, (direction, content) in enumerate(today_messages):
        timestamp = today_morning + timedelta(minutes=i*10)
        WhatsAppMessage.objects.create(
            client=auth_client,
            content=content,
            message_type=direction,
            direction=direction,
            timestamp=tz.localize(timestamp),
            message_id=f"test_today_{i}"
        )
    
    total_messages = len(yesterday_messages) + len(today_messages)
    print(f"✅ Criadas {total_messages} mensagens de teste")
    print(f"   📅 Ontem: {len(yesterday_messages)} mensagens")
    print(f"   📅 Hoje: {len(today_messages)} mensagens")
    
    return test_whatsapp

def test_context_loading():
    """Testa o carregamento do contexto conversacional"""
    print("\n🔍 TESTANDO CARREGAMENTO DE CONTEXTO")
    print("=" * 50)
    
    # Cria mensagens de teste
    test_whatsapp = create_test_messages()
    
    # Inicializa SmartAI Service
    ai_service = SmartAIService()
    
    # Simula uma nova mensagem (que deveria carregar contexto do banco)
    print(f"\n📨 Simulando nova mensagem para {test_whatsapp}...")
    test_message = "posso confirmar o reagendamento?"
    
    # Processa mensagem (isso deve carregar contexto do banco)
    response = ai_service.process_message(
        message_text=test_message,
        client_whatsapp=test_whatsapp,
        client_name="Cliente Teste"
    )
    
    # Verifica se o contexto foi carregado
    context = ai_service.conversation_context.get(test_whatsapp, {})
    
    print(f"\n📊 RESULTADOS DO TESTE:")
    print(f"   💬 Mensagens no contexto: {len(context.get('messages', []))}")
    print(f"   📝 Itens no resumo: {len(context.get('conversation_summary', []))}")
    print(f"   👤 Nome do cliente: {context.get('client_name', 'N/A')}")
    
    # Verifica mensagens por dia
    messages = context.get('messages', [])
    today = datetime.now().date()
    yesterday = today - timedelta(days=1)
    
    today_msgs = [m for m in messages if m.get('date') == today]
    yesterday_msgs = [m for m in messages if m.get('date') == yesterday]
    
    print(f"   📅 Mensagens de ontem: {len(yesterday_msgs)}")
    print(f"   📅 Mensagens de hoje: {len(today_msgs)}")
    
    # Mostra resumo conversacional
    if context.get('conversation_summary'):
        print(f"\n📋 RESUMO CONVERSACIONAL:")
        for i, summary_item in enumerate(context['conversation_summary'], 1):
            print(f"   {i}. {summary_item}")
    
    # Mostra estado da conversa
    if context.get('last_availability_check'):
        check = context['last_availability_check']
        date_str = check['datetime'].strftime('%d/%m às %H:%M')
        print(f"\n⏰ ÚLTIMA CONSULTA DE DISPONIBILIDADE: {date_str}")
    
    if context.get('pending_appointment'):
        pending = context['pending_appointment']
        date_str = pending['datetime'].strftime('%d/%m às %H:%M')
        print(f"📅 AGENDAMENTO PENDENTE: {date_str} (status: {pending['status']})")
    
    print(f"\n🤖 RESPOSTA DA IA:")
    print(f"   {response}")
    
    return context

def show_context_for_gpt(context, client_whatsapp):
    """Mostra como o contexto aparece para o GPT"""
    print(f"\n📄 CONTEXTO ENVIADO PARA O GPT:")
    print("=" * 50)
    
    ai_service = SmartAIService()
    gpt_context = ai_service._get_conversation_context_for_gpt(client_whatsapp)
    
    print(gpt_context)

if __name__ == "__main__":
    print("🧪 TESTE DE PERSISTÊNCIA DE CONTEXTO CONVERSACIONAL")
    print("=" * 60)
    
    # Executa teste
    context = test_context_loading()
    
    # Mostra contexto para GPT
    if context:
        show_context_for_gpt(context, "5511999999999")
    
    print(f"\n✅ TESTE CONCLUÍDO!")
    print("=" * 60) 