#!/usr/bin/env python3

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def fix_table_columns():
    """Adiciona colunas faltantes na tabela whatsapp_whatsappmessage"""
    
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
        print("🔧 Adicionando colunas faltantes...")
        
        # Listar colunas existentes
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'whatsapp_whatsappmessage'
            ORDER BY column_name;
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 Colunas existentes: {existing_columns}")
        
        # Colunas necessárias
        columns_to_add = [
            ("media_url", "VARCHAR(500)"),
            ("media_type", "VARCHAR(50)"),
            ("status", "VARCHAR(50) NOT NULL DEFAULT 'sent'"),
            ("processed_by_ai", "BOOLEAN NOT NULL DEFAULT false"),
            ("direction", "VARCHAR(20) NOT NULL DEFAULT 'RECEIVED'"),
            ("is_from_me", "BOOLEAN NOT NULL DEFAULT false"),
            ("remote_jid", "VARCHAR(255)"),
            ("push_name", "VARCHAR(255)")
        ]
        
        # Adicionar colunas se não existirem
        for column_name, column_def in columns_to_add:
            if column_name not in existing_columns:
                print(f"➕ Adicionando coluna: {column_name}")
                cursor.execute(f"ALTER TABLE whatsapp_whatsappmessage ADD COLUMN {column_name} {column_def};")
            else:
                print(f"✅ Coluna já existe: {column_name}")
        
        # Verificar se coluna message_type existe, se não criar
        if 'message_type' not in existing_columns:
            print("➕ Adicionando coluna: message_type")
            cursor.execute("ALTER TABLE whatsapp_whatsappmessage ADD COLUMN message_type VARCHAR(50) NOT NULL DEFAULT 'text';")
        
        # Remover constraint única antiga se existir
        try:
            cursor.execute("ALTER TABLE whatsapp_whatsappmessage DROP CONSTRAINT IF EXISTS whatsapp_whatsappmessage_message_id_remote_jid_key;")
        except:
            pass
            
        # Adicionar nova constraint única
        try:
            cursor.execute("ALTER TABLE whatsapp_whatsappmessage ADD CONSTRAINT unique_message_remote_jid UNIQUE (message_id, remote_jid);")
        except:
            print("⚠️ Constraint única já existe")
        
        print("✅ Colunas adicionadas com sucesso!")
        
        # Verificar estrutura final
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_name = 'whatsapp_whatsappmessage'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print(f"\n📋 Estrutura final da tabela:")
        for col in columns:
            print(f"   - {col[0]} ({col[1]}) - Nullable: {col[2]} - Default: {col[3]}")
            
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False
        
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    success = fix_table_columns()
    print(f"\n{'✅ Sucesso!' if success else '❌ Falhou!'}")
    
    if success:
        print("\n🎉 Tabela corrigida! Agora o sistema pode salvar mensagens do WhatsApp!")