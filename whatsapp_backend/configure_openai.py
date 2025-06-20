#!/usr/bin/env python3
"""
Script para configurar a chave da API do OpenAI
"""

import os
import sys

def configure_openai():
    print("🤖 Configuração da API do OpenAI")
    print("=" * 50)
    
    # Verifica se já existe uma chave configurada
    current_key = os.getenv('OPENAI_API_KEY', '')
    if current_key and current_key != 'your-openai-api-key-here':
        print(f"✅ Chave da API já configurada: {current_key[:10]}...")
        response = input("Deseja alterar a chave? (s/n): ").lower()
        if response != 's':
            print("Configuração mantida.")
            return
    
    print("\n📋 Para obter sua chave da API do OpenAI:")
    print("1. Acesse: https://platform.openai.com/api-keys")
    print("2. Faça login na sua conta OpenAI")
    print("3. Clique em 'Create new secret key'")
    print("4. Copie a chave gerada (começa com 'sk-')")
    print("\n⚠️  IMPORTANTE: Mantenha sua chave segura e não a compartilhe!")
    
    api_key = input("\n🔑 Cole sua chave da API do OpenAI: ").strip()
    
    if not api_key:
        print("❌ Nenhuma chave fornecida. Configuração cancelada.")
        return
    
    if not api_key.startswith('sk-'):
        print("❌ Chave inválida! A chave deve começar com 'sk-'")
        return
    
    # Salva a chave no arquivo .env
    env_file = '.env'
    env_content = []
    
    # Lê o arquivo .env existente se existir
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            env_content = f.readlines()
    
    # Procura pela linha OPENAI_API_KEY
    key_found = False
    for i, line in enumerate(env_content):
        if line.startswith('OPENAI_API_KEY='):
            env_content[i] = f'OPENAI_API_KEY={api_key}\n'
            key_found = True
            break
    
    # Se não encontrou, adiciona a linha
    if not key_found:
        env_content.append(f'OPENAI_API_KEY={api_key}\n')
    
    # Escreve o arquivo .env
    with open(env_file, 'w') as f:
        f.writelines(env_content)
    
    print(f"✅ Chave da API configurada com sucesso!")
    print(f"📁 Configuração salva em: {os.path.abspath(env_file)}")
    print("\n🔄 Reinicie o servidor Django para aplicar as mudanças.")
    print("   python manage.py runserver 0.0.0.0:8000")

def test_openai_connection():
    """Testa a conexão com a API do OpenAI"""
    try:
        import openai
        from django.conf import settings
        
        # Configura o Django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
        import django
        django.setup()
        
        # Testa a conexão
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Olá! Teste de conexão."}],
            max_tokens=10
        )
        
        print("✅ Conexão com OpenAI testada com sucesso!")
        print(f"📝 Resposta: {response.choices[0].message.content}")
        
    except Exception as e:
        print(f"❌ Erro ao testar conexão: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        test_openai_connection()
    else:
        configure_openai() 