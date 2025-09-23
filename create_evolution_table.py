#!/usr/bin/env python3

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_evolution_table():
    """Cria a tabela whatsapp_evolutionconfig diretamente no PostgreSQL"""
    
    # Conectar ao PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        port="5432",
        database="whatsapp_db",
        user="postgres",
        password="postgres123"
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
        print("🔧 Criando tabela whatsapp_evolutionconfig...")
        
        # Verificar se a tabela já existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'whatsapp_evolutionconfig'
            );
        """)
        
        if cursor.fetchone()[0]:
            print("✅ Tabela já existe!")
        else:
            # Criar a tabela
            cursor.execute("""
                CREATE TABLE whatsapp_evolutionconfig (
                    id SERIAL PRIMARY KEY,
                    instance_id VARCHAR(100) NOT NULL,
                    api_key VARCHAR(255) NOT NULL,
                    webhook_url VARCHAR(500) NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT true,
                    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)
            print("✅ Tabela criada!")
        
        # Verificar se já existe configuração
        cursor.execute("SELECT COUNT(*) FROM whatsapp_evolutionconfig WHERE is_active = true;")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("📝 Inserindo configuração Evolution...")
            cursor.execute("""
                INSERT INTO whatsapp_evolutionconfig 
                (instance_id, api_key, webhook_url, is_active, created_at, updated_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
            """, (
                "Elo",
                "0891579bb8dda6a54deb403b0c01241c",
                "http://155.133.22.207:8000/api/whatsapp/webhook/evolution/",
                True
            ))
            print("✅ Configuração inserida!")
        else:
            print("✅ Configuração já existe!")
            # Atualizar webhook URL
            cursor.execute("""
                UPDATE whatsapp_evolutionconfig 
                SET webhook_url = %s, updated_at = CURRENT_TIMESTAMP
                WHERE is_active = true;
            """, ("http://155.133.22.207:8000/api/whatsapp/webhook/evolution/",))
            print("🔄 Webhook URL atualizada!")
        
        # Mostrar configuração atual
        cursor.execute("SELECT * FROM whatsapp_evolutionconfig WHERE is_active = true;")
        config = cursor.fetchone()
        
        if config:
            print(f"\n📋 Configuração atual:")
            print(f"   ID: {config[0]}")
            print(f"   Instância: {config[1]}")
            print(f"   API Key: {config[2][:20]}...")
            print(f"   Webhook: {config[3]}")
            print(f"   Ativa: {config[4]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    success = create_evolution_table()
    print(f"\n{'✅ Sucesso!' if success else '❌ Falhou!'}")
    
    if success:
        print("\n🎉 A tabela foi criada! Agora teste o webhook novamente.")