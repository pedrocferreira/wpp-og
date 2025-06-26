-- Configurações iniciais do PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Configurar timezone
SET timezone = 'America/Sao_Paulo';

-- Criar usuário adicional se necessário
-- CREATE USER whatsapp_user WITH ENCRYPTED PASSWORD 'whatsapp_pass';
-- GRANT ALL PRIVILEGES ON DATABASE whatsapp_db TO whatsapp_user; 