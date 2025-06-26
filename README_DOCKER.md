# 🐳 WhatsApp Atendimento - Docker Setup

Esta documentação explica como executar o projeto usando Docker, facilitando o desenvolvimento e deployment.

## 📋 Pré-requisitos

- Docker (versão 20.10+)
- Docker Compose (versão 2.0+)
- Git

## 🏗️ Arquitetura do Sistema

O projeto é dividido em containers Docker:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   PostgreSQL    │
│   (Angular)     │◄──►│   (Django)      │◄──►│   Database      │
│   Nginx:80      │    │   Port:8000     │    │   Port:5432     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Celery Worker  │◄──►│     Redis       │
                       │  (Background)   │    │   Port:6379     │
                       └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  Celery Beat    │
                       │  (Scheduler)    │
                       └─────────────────┘
```

## 🚀 Início Rápido

### 1. Clonar o Repositório
```bash
git clone <seu-repositorio>
cd wpp-og
```

### 2. Configurar Variáveis de Ambiente
```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar com suas configurações
nano .env
```

### 3. Executar em Desenvolvimento
```bash
# Construir e iniciar todos os serviços
docker-compose up --build

# Ou em background
docker-compose up -d --build
```

### 4. Acessar o Sistema
- **Frontend**: http://localhost
- **Admin Django**: http://localhost/admin
- **API**: http://localhost/api

**Credenciais padrão**: `admin` / `admin123`

## 🔧 Comandos Úteis

### Gerenciamento dos Containers
```bash
# Ver status dos containers
docker-compose ps

# Ver logs de todos os serviços
docker-compose logs -f

# Ver logs de um serviço específico
docker-compose logs -f backend

# Parar todos os serviços
docker-compose down

# Parar e remover volumes (CUIDADO: perde dados!)
docker-compose down -v

# Reconstruir apenas um serviço
docker-compose build backend
docker-compose up -d backend
```

### Comandos Django no Container
```bash
# Executar migrações
docker-compose exec backend python manage.py migrate

# Criar superusuário
docker-compose exec backend python manage.py createsuperuser

# Coletar arquivos estáticos
docker-compose exec backend python manage.py collectstatic

# Acessar shell do Django
docker-compose exec backend python manage.py shell

# Acessar bash do container
docker-compose exec backend bash
```

### Comandos do Banco de Dados
```bash
# Acessar PostgreSQL
docker-compose exec db psql -U postgres -d whatsapp_db

# Backup do banco
docker-compose exec db pg_dump -U postgres whatsapp_db > backup.sql

# Restaurar backup
docker-compose exec -T db psql -U postgres -d whatsapp_db < backup.sql
```

## 🌍 Deployment em Produção

### 1. Configurar Variáveis de Produção
```bash
# Criar arquivo .env.prod
cp .env.example .env.prod

# Configurar para produção
DEBUG=False
DJANGO_SECRET_KEY=sua-chave-super-segura
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com
DB_PASSWORD=senha-super-segura
```

### 2. Executar em Produção
```bash
# Usar docker-compose de produção
docker-compose -f docker-compose.prod.yml up -d --build

# Aplicar migrações
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Criar superusuário
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser
```

### 3. Configurar SSL (Opcional)
```bash
# Criar diretório para certificados
mkdir -p docker/ssl

# Copiar seus certificados SSL
cp seu-certificado.crt docker/ssl/
cp sua-chave-privada.key docker/ssl/

# Atualizar configuração do nginx se necessário
```

## 🔍 Monitoramento e Logs

### Ver Logs em Tempo Real
```bash
# Todos os serviços
docker-compose logs -f

# Apenas backend
docker-compose logs -f backend

# Apenas frontend
docker-compose logs -f frontend

# Apenas Celery
docker-compose logs -f celery
```

### Verificar Status dos Serviços
```bash
# Status dos containers
docker-compose ps

# Estatísticas de recursos
docker stats

# Verificar saúde dos serviços
docker-compose exec backend python manage.py check
```

## 🛠️ Desenvolvimento

### Hot Reload
O projeto está configurado para hot reload:
- **Backend**: Volumes mapeados para `/app`
- **Frontend**: Reconstrução necessária para mudanças

### Debugger
Para usar debugger no Django:
```python
# Adicionar no código
import pdb; pdb.set_trace()
```

```bash
# Anexar ao container para interagir com debugger
docker-compose exec backend python manage.py runserver 0.0.0.0:8000
```

### Executar Testes
```bash
# Testes do backend
docker-compose exec backend python manage.py test

# Testes do frontend
docker-compose exec frontend npm test
```

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. Container não inicia
```bash
# Ver logs do container
docker-compose logs backend

# Verificar se as portas estão livres
netstat -tlnp | grep :8000
```

#### 2. Banco de dados não conecta
```bash
# Verificar se PostgreSQL está rodando
docker-compose ps db

# Testar conexão manual
docker-compose exec backend python manage.py dbshell
```

#### 3. Problemas de permissão
```bash
# Reconstruir com permissões corretas
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

#### 4. Frontend não carrega
```bash
# Verificar build do Angular
docker-compose logs frontend

# Reconstruir frontend
docker-compose build frontend
docker-compose up -d frontend
```

### Reset Completo
Se tudo der errado, reset completo:
```bash
# CUIDADO: Remove todos os dados!
docker-compose down -v
docker system prune -a
docker volume prune

# Reconstruir tudo
docker-compose up --build
```

## 📊 Variáveis de Ambiente

### Obrigatórias
```env
DJANGO_SECRET_KEY=sua-chave-secreta
EVOLUTION_API_KEY=sua-chave-evolution
EVOLUTION_INSTANCE_ID=sua-instancia
```

### Opcionais
```env
DEBUG=True
DB_NAME=whatsapp_db
DB_USER=postgres
DB_PASSWORD=postgres123
OPENAI_API_KEY=sua-chave-openai
```

## 🔒 Segurança

### Em Produção
- [ ] Alterar senhas padrão
- [ ] Configurar SSL/HTTPS
- [ ] Usar secrets para chaves sensíveis
- [ ] Configurar backup automático
- [ ] Monitorar logs de segurança

### Backup Automático
```bash
# Criar script de backup
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U postgres whatsapp_db > "backup_${DATE}.sql"
```

## 💡 Dicas

1. **Performance**: Use SSD para volumes Docker
2. **Desenvolvimento**: Use `docker-compose.override.yml` para configurações locais
3. **Logs**: Configure rotação de logs em produção
4. **Monitoramento**: Considere usar Portainer para interface gráfica
5. **CI/CD**: Integre com GitHub Actions para deploy automático

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs: `docker-compose logs -f`
2. Consulte a documentação oficial do Docker
3. Abra uma issue no repositório

---

**Happy Coding! 🚀** 