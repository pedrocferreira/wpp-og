# WhatsApp Atendimento Inteligente

Sistema de atendimento automatizado via WhatsApp usando IA para agendamento de consultas.

## Estrutura do Projeto

### Backend (Django)
- API REST para gerenciamento de consultas
- Integração com Evolution API WhatsApp
- Sistema de IA para respostas automáticas
- Gestão de agendamentos e lembretes

### Frontend (Angular)
- Dashboard para atendentes
- Interface de gerenciamento de consultas
- Visualização de conversas WhatsApp
- Calendário de agendamentos

## Requisitos

### Backend
- Python 3.8+
- Django 4.2+
- Django REST Framework
- Celery (para tarefas agendadas)
- PostgreSQL
- Redis

### Frontend
- Node.js 16+
- Angular 16+
- Angular Material
- RxJS

## Configuração do Ambiente

1. Clone o repositório:
```bash
git clone <repository-url>
cd whatsapp-dashboard
```

2. Configure o ambiente virtual Python:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
.\venv\Scripts\activate  # Windows
```

3. Instale as dependências do backend:
```bash
cd whatsapp_backend
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
# Crie um arquivo .env na raiz do projeto backend
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
DB_NAME=whatsapp_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
EVOLUTION_API_URL=https://evolution.og-trk.xyz
EVOLUTION_API_KEY=your-api-key
OPENAI_API_KEY=your-openai-api-key
```

5. Configure o banco de dados:
```bash
python manage.py migrate
python manage.py createsuperuser
```

6. Instale as dependências do frontend:
```bash
cd ../frontend
npm install
```

## Executando o Projeto

1. Inicie o Redis:
```bash
redis-server
```

2. Inicie o Celery:
```bash
cd whatsapp_backend
celery -A whatsapp_backend worker -l info
celery -A whatsapp_backend beat -l info
```

3. Inicie o backend:
```bash
cd whatsapp_backend
python manage.py runserver
```

4. Inicie o frontend:
```bash
cd frontend
ng serve
```

5. Acesse:
- Frontend: http://localhost:4200
- Admin Django: http://localhost:8000/admin
- API: http://localhost:8000/api

## Configuração do Webhook

1. Acesse o painel de administração da Evolution API
2. Configure o webhook para: http://seu-dominio/api/webhook/
3. Ative o webhook para receber as mensagens

## Funcionalidades

- [ ] Autenticação de usuários (atendentes)
- [ ] Integração com Evolution API WhatsApp
- [ ] Dashboard de atendimentos
- [ ] Sistema de agendamento de consultas
- [ ] Respostas automáticas com IA
- [ ] Sistema de lembretes automáticos
- [ ] Histórico de conversas
- [ ] Relatórios de atendimento

## Contribuindo

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para mais detalhes. 