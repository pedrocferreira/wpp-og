#!/usr/bin/env python
"""
Script de teste rápido para verificar as melhorias no SmartAI
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from whatsapp.smart_ai_service import SmartAIService
from whatsapp.natural_language_processor import NaturalLanguageProcessor

def test_melhorias():
    print("🧪 TESTANDO MELHORIAS DO SMARTAI...")
    print("=" * 50)
    
    # Inicializa serviços
    service = SmartAIService()
    nlp = NaturalLanguageProcessor()
    
    print(f"✅ OpenAI disponível: {service.openai_available}")
    print()
    
    # Testa detecção de consultas existentes
    consulta_texts = [
        "Quando é minha proxima consulta?",
        "quando minha consulta",
        "que dia consulta",
        "horario consulta"
    ]
    
    print("🔍 TESTE: Detecção de Consultas Existentes")
    for text in consulta_texts:
        result = service._is_consultation_inquiry(text)
        print(f"   '{text}' -> {result}")
    print()
    
    # Testa detecção de agendamentos
    agendamento_texts = [
        "Quero amanha as 18",
        "quero as 15h",
        "quinta feira 14h",
        "hoje 16:00"
    ]
    
    print("📅 TESTE: Detecção de Agendamentos")
    for text in agendamento_texts:
        result = nlp.extract_appointment_intent(text)
        datetime_result = nlp.extract_datetime(text)
        print(f"   '{text}' -> Intent: {result}, DateTime: {datetime_result}")
    print()
    
    # Testa detecção de disponibilidade
    disponibilidade_texts = [
        "as 15 tem?",
        "14h tem vaga?",
        "amanha as 10 ta livre?"
    ]
    
    print("❓ TESTE: Detecção de Disponibilidade")
    for text in disponibilidade_texts:
        result = service._is_availability_question(text)
        print(f"   '{text}' -> {result}")
    print()
    
    print("✅ Testes concluídos!")

if __name__ == "__main__":
    test_melhorias() 