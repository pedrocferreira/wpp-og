#!/usr/bin/env python3

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def create_whatsapp_tables():
    """Cria as tabelas do WhatsApp faltantes no PostgreSQL"""
    
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
        print("🔧 Criando tabelas do WhatsApp...")
        
        # 1. Tabela authentication_authclient (clientes/usuários WhatsApp)
        print("📝 Criando tabela authentication_authclient...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS authentication_authclient (
                id SERIAL PRIMARY KEY,
                phone VARCHAR(20) NOT NULL UNIQUE,
                name VARCHAR(255),
                is_active BOOLEAN NOT NULL DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 2. Tabela whatsapp_whatsappmessage (mensagens)
        print("📝 Criando tabela whatsapp_whatsappmessage...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_whatsappmessage (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES authentication_authclient(id) ON DELETE CASCADE,
                message_id VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                is_from_me BOOLEAN NOT NULL DEFAULT false,
                message_type VARCHAR(50) NOT NULL DEFAULT 'text',
                remote_jid VARCHAR(255) NOT NULL,
                push_name VARCHAR(255),
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(message_id, remote_jid)
            );
        """)
        
        # 3. Tabela whatsapp_airesponse (respostas da IA)
        print("📝 Criando tabela whatsapp_airesponse...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS whatsapp_airesponse (
                id SERIAL PRIMARY KEY,
                original_message_id INTEGER REFERENCES whatsapp_whatsappmessage(id) ON DELETE CASCADE,
                response_content TEXT NOT NULL,
                response_type VARCHAR(50) NOT NULL DEFAULT 'text',
                processed_by_id INTEGER REFERENCES authentication_user(id) ON DELETE SET NULL,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # 4. Índices para performance
        print("📝 Criando índices...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_whatsapp_message_remote_jid ON whatsapp_whatsappmessage(remote_jid);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_whatsapp_message_timestamp ON whatsapp_whatsappmessage(timestamp);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_whatsapp_message_client ON whatsapp_whatsappmessage(client_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_authclient_phone ON authentication_authclient(phone);")
        
        print("✅ Todas as tabelas criadas com sucesso!")
        
        # Verificar tabelas criadas
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('authentication_authclient', 'whatsapp_whatsappmessage', 'whatsapp_airesponse', 'whatsapp_evolutionconfig')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"\n📋 Tabelas WhatsApp disponíveis:")
        for table in tables:
            print(f"   ✅ {table[0]}")
        
        # Inserir um cliente de teste se não existir
        cursor.execute("SELECT COUNT(*) FROM authentication_authclient;")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("\n👤 Criando cliente de teste...")
            cursor.execute("""
                INSERT INTO authentication_authclient (phone, name, is_active)
                VALUES ('5511999999999', 'Cliente Teste', true);
            """)
            print("✅ Cliente de teste criado!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    success = create_whatsapp_tables()
    print(f"\n{'✅ Sucesso!' if success else '❌ Falhou!'}")
    
    if success:
        print("\n🎉 Tabelas criadas! O sistema agora pode processar mensagens do WhatsApp!")