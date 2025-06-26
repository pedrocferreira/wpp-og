#!/bin/bash

# Script de início rápido para WhatsApp Atendimento
# Autor: Assistant
# Data: $(date +%Y-%m-%d)

set -e  # Parar em caso de erro

echo "🐳 WhatsApp Atendimento - Setup Docker"
echo "======================================"

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para logs coloridos
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar se Docker está instalado
check_docker() {
    log_info "Verificando Docker..."
    if ! command -v docker &> /dev/null; then
        log_error "Docker não está instalado!"
        echo "Instale o Docker: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose não está instalado!"
        echo "Instale o Docker Compose: https://docs.docker.com/compose/install/"
        exit 1
    fi
    
    log_success "Docker e Docker Compose estão instalados"
}

# Verificar se Docker está rodando
check_docker_running() {
    log_info "Verificando se Docker está rodando..."
    if ! docker info &> /dev/null; then
        log_error "Docker não está rodando!"
        echo "Inicie o Docker daemon"
        exit 1
    fi
    log_success "Docker está rodando"
}

# Criar arquivo .env se não existir
setup_env() {
    log_info "Configurando variáveis de ambiente..."
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            log_success "Arquivo .env criado a partir do exemplo"
            log_warning "IMPORTANTE: Edite o arquivo .env com suas configurações reais!"
            log_warning "Especialmente: EVOLUTION_API_KEY, OPENAI_API_KEY"
        else
            log_error "Arquivo .env.example não encontrado!"
            exit 1
        fi
    else
        log_info "Arquivo .env já existe"
    fi
}

# Construir e iniciar containers
start_containers() {
    log_info "Construindo e iniciando containers..."
    log_info "Isso pode demorar na primeira vez..."
    
    # Parar containers existentes se houver
    docker-compose down 2>/dev/null || true
    
    # Construir e iniciar
    if docker-compose up -d --build; then
        log_success "Containers iniciados com sucesso"
    else
        log_error "Falha ao iniciar containers"
        exit 1
    fi
}

# Aguardar serviços estarem prontos
wait_for_services() {
    log_info "Aguardando serviços ficarem prontos..."
    
    # Aguardar banco de dados
    log_info "Aguardando PostgreSQL..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T db pg_isready -U postgres &>/dev/null; then
            break
        fi
        sleep 2
        timeout=$((timeout-2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "PostgreSQL não ficou pronto a tempo"
        exit 1
    fi
    
    # Aguardar Redis
    log_info "Aguardando Redis..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker-compose exec -T redis redis-cli ping &>/dev/null; then
            break
        fi
        sleep 1
        timeout=$((timeout-1))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "Redis não ficou pronto a tempo"
        exit 1
    fi
    
    log_success "Todos os serviços estão prontos"
}

# Executar migrações
run_migrations() {
    log_info "Executando migrações do Django..."
    if docker-compose exec backend python manage.py migrate; then
        log_success "Migrações executadas com sucesso"
    else
        log_error "Falha nas migrações"
        exit 1
    fi
}

# Criar superusuário
create_superuser() {
    log_info "Verificando superusuário..."
    
    # Verificar se já existe
    if docker-compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
exit(0 if User.objects.filter(username='admin').exists() else 1)
" 2>/dev/null; then
        log_info "Superusuário 'admin' já existe"
    else
        log_info "Criando superusuário padrão..."
        docker-compose exec backend python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
print('Superusuário criado: admin/admin123')
"
        log_success "Superusuário criado: admin/admin123"
    fi
}

# Mostrar status final
show_status() {
    log_info "Status dos containers:"
    docker-compose ps
    
    echo ""
    log_success "🎉 Setup concluído com sucesso!"
    echo ""
    echo "📱 Acesse o sistema:"
    echo "   Frontend: http://localhost"
    echo "   Admin:    http://localhost/admin"
    echo "   API:      http://localhost/api"
    echo ""
    echo "🔐 Credenciais padrão:"
    echo "   Usuário: admin"
    echo "   Senha:   admin123"
    echo ""
    echo "📋 Comandos úteis:"
    echo "   Ver logs:    make logs"
    echo "   Parar:       make down"
    echo "   Reiniciar:   make restart"
    echo "   Ajuda:       make help"
    echo ""
    log_warning "📝 Lembre-se de editar o arquivo .env com suas configurações reais!"
}

# Menu principal
main() {
    echo ""
    echo "Este script irá:"
    echo "1. Verificar Docker"
    echo "2. Configurar ambiente (.env)"
    echo "3. Construir containers"
    echo "4. Iniciar serviços"
    echo "5. Executar migrações"
    echo "6. Criar superusuário"
    echo ""
    
    read -p "Deseja continuar? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        log_info "Operação cancelada"
        exit 0
    fi
    
    # Executar steps
    check_docker
    check_docker_running
    setup_env
    start_containers
    wait_for_services
    run_migrations
    create_superuser
    show_status
}

# Executar script
main "$@" 