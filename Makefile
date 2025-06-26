# Makefile para WhatsApp Atendimento
.PHONY: help build up down logs shell migrate test clean backup

# Variáveis
COMPOSE_FILE = docker-compose.yml
COMPOSE_FILE_PROD = docker-compose.prod.yml

help: ## Mostrar esta ajuda
	@echo "WhatsApp Atendimento - Comandos Docker"
	@echo "======================================"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# === DESENVOLVIMENTO ===
build: ## Construir todos os containers
	docker-compose -f $(COMPOSE_FILE) build

up: ## Iniciar todos os serviços
	docker-compose -f $(COMPOSE_FILE) up -d

up-build: ## Construir e iniciar todos os serviços
	docker-compose -f $(COMPOSE_FILE) up -d --build

down: ## Parar todos os serviços
	docker-compose -f $(COMPOSE_FILE) down

restart: ## Reiniciar todos os serviços
	docker-compose -f $(COMPOSE_FILE) restart

logs: ## Ver logs de todos os serviços
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-backend: ## Ver logs do backend
	docker-compose -f $(COMPOSE_FILE) logs -f backend

logs-frontend: ## Ver logs do frontend
	docker-compose -f $(COMPOSE_FILE) logs -f frontend

logs-celery: ## Ver logs do Celery
	docker-compose -f $(COMPOSE_FILE) logs -f celery

status: ## Ver status dos containers
	docker-compose -f $(COMPOSE_FILE) ps

# === DJANGO ===
shell: ## Acessar shell do Django
	docker-compose -f $(COMPOSE_FILE) exec backend python manage.py shell

bash: ## Acessar bash do container backend
	docker-compose -f $(COMPOSE_FILE) exec backend bash

migrate: ## Executar migrações
	docker-compose -f $(COMPOSE_FILE) exec backend python manage.py migrate

makemigrations: ## Criar migrações
	docker-compose -f $(COMPOSE_FILE) exec backend python manage.py makemigrations

createsuperuser: ## Criar superusuário
	docker-compose -f $(COMPOSE_FILE) exec backend python manage.py createsuperuser

collectstatic: ## Coletar arquivos estáticos
	docker-compose -f $(COMPOSE_FILE) exec backend python manage.py collectstatic --noinput

# === DATABASE ===
db-shell: ## Acessar shell do PostgreSQL
	docker-compose -f $(COMPOSE_FILE) exec db psql -U postgres -d whatsapp_db

backup: ## Fazer backup do banco de dados
	docker-compose -f $(COMPOSE_FILE) exec -T db pg_dump -U postgres whatsapp_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore: ## Restaurar backup (uso: make restore FILE=backup.sql)
	docker-compose -f $(COMPOSE_FILE) exec -T db psql -U postgres -d whatsapp_db < $(FILE)

# === TESTES ===
test: ## Executar testes do backend
	docker-compose -f $(COMPOSE_FILE) exec backend python manage.py test

test-frontend: ## Executar testes do frontend
	docker-compose -f $(COMPOSE_FILE) exec frontend npm test

# === PRODUÇÃO ===
prod-build: ## Construir para produção
	docker-compose -f $(COMPOSE_FILE_PROD) build

prod-up: ## Iniciar em produção
	docker-compose -f $(COMPOSE_FILE_PROD) up -d

prod-down: ## Parar produção
	docker-compose -f $(COMPOSE_FILE_PROD) down

prod-logs: ## Ver logs da produção
	docker-compose -f $(COMPOSE_FILE_PROD) logs -f

prod-migrate: ## Executar migrações em produção
	docker-compose -f $(COMPOSE_FILE_PROD) exec backend python manage.py migrate

prod-collectstatic: ## Coletar statics em produção
	docker-compose -f $(COMPOSE_FILE_PROD) exec backend python manage.py collectstatic --noinput

# === LIMPEZA ===
clean: ## Limpar containers e imagens não utilizadas
	docker system prune -f

clean-all: ## Limpar tudo (CUIDADO: remove volumes!)
	docker-compose -f $(COMPOSE_FILE) down -v
	docker system prune -a -f
	docker volume prune -f

# === MONITORAMENTO ===
stats: ## Ver estatísticas dos containers
	docker stats

# === UTILITÁRIOS ===
env-example: ## Criar arquivo .env a partir do exemplo
	cp .env.example .env
	@echo "Arquivo .env criado! Edite com suas configurações."

setup: env-example build up migrate createsuperuser ## Setup completo do projeto
	@echo "Setup completo! Acesse http://localhost"

# === DESENVOLVIMENTO AVANÇADO ===
rebuild-backend: ## Reconstruir apenas o backend
	docker-compose -f $(COMPOSE_FILE) build backend
	docker-compose -f $(COMPOSE_FILE) up -d backend

rebuild-frontend: ## Reconstruir apenas o frontend
	docker-compose -f $(COMPOSE_FILE) build frontend
	docker-compose -f $(COMPOSE_FILE) up -d frontend

# === DEBUG ===
debug-backend: ## Executar backend em modo debug
	docker-compose -f $(COMPOSE_FILE) exec backend python manage.py runserver 0.0.0.0:8000

debug-logs: ## Ver logs detalhados
	docker-compose -f $(COMPOSE_FILE) logs -f --tail=100 