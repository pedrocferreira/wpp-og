#!/usr/bin/env python3
"""
Teste simples do sistema de contexto
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from whatsapp.smart_ai_service import SmartAIService

def test_simple():
    print("🧪 TESTE SIMPLES DE CONTEXTO")
    print("=" * 40)
    
    # Inicializa SmartAI
    ai_service = SmartAIService()
    print("✅ SmartAI inicializado")
    
    # Simula mensagem de um cliente
    test_whatsapp = "5511888888888"
    
    # Primeira mensagem
    response1 = ai_service.process_message("Oi", test_whatsapp, "João Teste")
    print(f"📨 Primeira: Oi")
    print(f"🤖 Resposta: {response1[:50]}...")
    
    # Segunda mensagem (deve lembrar do contexto)
    response2 = ai_service.process_message("Quero agendar", test_whatsapp)
    print(f"📨 Segunda: Quero agendar")
    print(f"🤖 Resposta: {response2[:50]}...")
    
    # Verifica contexto
    context = ai_service.conversation_context.get(test_whatsapp, {})
    print(f"💬 Mensagens no contexto: {len(context.get('messages', []))}")
    print(f"👤 Nome lembrado: {context.get('client_name', 'N/A')}")
    
    print("✅ Teste concluído!")

if __name__ == "__main__":
    test_simple() 