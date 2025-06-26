# Sistema de Atendimento via WhatsApp com IA

Este é um sistema de atendimento automatizado via WhatsApp que utiliza Inteligência Artificial para processar e responder mensagens. O sistema é composto por um backend Django e integração com a Evolution API para comunicação com o WhatsApp.

## Arquitetura

O sistema é composto por:

1. **Backend (Django)**
   - Autenticação JWT
   - API REST
   - Sistema de IA para respostas automáticas
   - Integração com Evolution API
   - SQLite como banco de dados
   - Sistema de agendamento com Celery

2. **Evolution API**
   - API de integração com WhatsApp
   - Rodando em container Docker
   - Gerenciamento de conexões WhatsApp

## Pré-requisitos

- Python 3.8+
- Docker e Docker Compose
- Redis (para Celery)
- Evolution API rodando em container

## Rodando o Projeto

### Ambiente de Desenvolvimento

1. **Preparar o ambiente**
```bash
# Clone o repositório
git clone [URL_DO_REPOSITORIO]
cd wpp-og

# Crie e ative o ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows

# Instale as dependências
cd whatsapp_backend
pip install -r requirements.txt
```

2. **Configurar as variáveis de ambiente**
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite o arquivo .env com suas configurações
nano .env
```

3. **Configurar o banco de dados**
```bash
# Aplique as migrações
python manage.py migrate

# Crie um superusuário (opcional)
python manage.py createsuperuser
```

4. **Configurar o Evolution API**
```bash
# Inicie o container do Evolution API
docker-compose up -d evolution

# Configure a instância
python manage.py setup_evolution
```

5. **Iniciar os serviços**
```bash
# Terminal 1: Redis
redis-server

# Terminal 2: Celery
celery -A whatsapp_backend worker -l info

# Terminal 3: Django
python manage.py runserver 0.0.0.0:8000
```

### Ambiente de Produção

1. **Preparar o servidor**
```bash
# Instale as dependências do sistema
sudo apt update
sudo apt install python3-pip python3-venv redis-server docker docker-compose nginx

# Clone o repositório
git clone [URL_DO_REPOSITORIO]
cd wpp-og

# Configure o ambiente virtual
python3 -m venv venv
source venv/bin/activate
pip install -r whatsapp_backend/requirements.txt
```

2. **Configurar o Docker**
```bash
# Crie a rede Docker
docker network create evolution-network

# Configure o Evolution API
docker-compose -f docker-compose.prod.yml up -d
```

3. **Configurar o Nginx**
```bash
# Copie a configuração do Nginx
sudo cp nginx/whatsapp.conf /etc/nginx/sites-available/
sudo ln -s /etc/nginx/sites-available/whatsapp.conf /etc/nginx/sites-enabled/

# Teste e reinicie o Nginx
sudo nginx -t
sudo systemctl restart nginx
```

4. **Configurar o Supervisor**
```bash
# Copie as configurações do Supervisor
sudo cp supervisor/*.conf /etc/supervisor/conf.d/

# Recarregue o Supervisor
sudo supervisorctl reread
sudo supervisorctl update
```

5. **Iniciar os serviços**
```bash
# Inicie todos os serviços
sudo supervisorctl start all
```

### Verificação do Sistema

1. **Verificar logs**
```bash
# Logs do Django
tail -f whatsapp_backend/logs/debug.log

# Logs do Celery
tail -f whatsapp_backend/logs/celery.log

# Logs do Evolution API
docker logs -f evolution
```

2. **Verificar status dos serviços**
```bash
# Status do Supervisor
sudo supervisorctl status

# Status do Docker
docker ps

# Status do Nginx
sudo systemctl status nginx
```

3. **Testar o sistema**
```bash
# Teste o webhook
curl -X POST http://localhost:8000/api/whatsapp/webhook/evolution/

# Verifique o status da conexão
curl http://localhost:8000/api/whatsapp/status/
```

### Scripts Úteis

1. **Reiniciar todos os serviços**
```bash
#!/bin/bash
# restart.sh
sudo supervisorctl restart all
docker-compose restart
sudo systemctl restart nginx
```

2. **Backup do sistema**
```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d)
mkdir -p backups/$DATE

# Backup do banco
python manage.py dumpdata > backups/$DATE/db.json

# Backup dos arquivos de mídia
tar -czf backups/$DATE/media.tar.gz media/

# Backup das configurações
cp .env backups/$DATE/
cp docker-compose.yml backups/$DATE/
```

3. **Atualizar o sistema**
```bash
#!/bin/bash
# update.sh
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart all
```

### Monitoramento

1. **Métricas importantes para monitorar**
- Uso de CPU e memória
- Tempo de resposta da API
- Número de mensagens processadas
- Taxa de sucesso/erro nas respostas
- Status da conexão WhatsApp

2. **Alertas**
- Erros 5xx no nginx
- Falhas na conexão WhatsApp
- Alto uso de CPU/memória
- Falhas no processamento de mensagens

3. **Dashboard (opcional)**
- Grafana para visualização de métricas
- Prometheus para coleta de dados
- AlertManager para gerenciamento de alertas

## Endpoints Principais

- `/api/whatsapp/webhook/evolution/`: Webhook para receber mensagens
- `/api/whatsapp/status/`: Status da conexão WhatsApp
- `/api/whatsapp/messages/`: Gerenciamento de mensagens

## Troubleshooting

### Erro 404 ao enviar mensagens

Se receber erro 404 ao enviar mensagens, verifique:
1. Se o `EVOLUTION_INSTANCE_ID` está correto no `.env`
2. Se a instância está conectada no Evolution API
3. Se a URL da Evolution API está correta e acessível

### Erro de conexão com Evolution API

Se houver erro de conexão:
1. Verifique se o container está rodando
2. Confirme se as portas estão expostas corretamente
3. Verifique se o domínio está resolvendo para o IP correto

### Mensagens não chegam ao webhook

Se as mensagens não chegarem:
1. Verifique se o webhook está configurado corretamente no Evolution API
2. Confirme se a URL do webhook está acessível externamente
3. Verifique os logs do Django para erros

## Logs e Monitoramento

O sistema usa o logger do Python para registrar eventos importantes:

- Logs de webhook: `/api/whatsapp/webhook/evolution/`
- Logs de mensagens: Todas as mensagens recebidas e enviadas
- Logs de IA: Processamento e respostas da IA
- Logs de erro: Erros e exceções do sistema

Para visualizar os logs em tempo real:
```bash
tail -f whatsapp_backend/logs/debug.log
```

## Segurança

1. **API Keys**: Mantenha suas chaves de API seguras e nunca as compartilhe
2. **Webhook**: Use HTTPS para o webhook em produção
3. **Autenticação**: Use JWT para autenticar requisições à API
4. **CORS**: Configure corretamente os CORS_ALLOWED_ORIGINS em produção

## Manutenção

1. **Backup do Banco**:
```bash
python manage.py dumpdata > backup.json
```

2. **Atualização do Sistema**:
```bash
git pull
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic
```

3. **Limpeza de Logs**:
```bash
truncate -s 0 whatsapp_backend/logs/debug.log
```

## Suporte

Para suporte ou dúvidas:
1. Verifique a documentação
2. Consulte os logs do sistema
3. Abra uma issue no repositório
4. Entre em contato com a equipe de suporte 


Email: admin@example.com
Senha: admin123
Opção 2 - Usuário Teste (novo):
Email: teste@teste.com
Senha: 123456