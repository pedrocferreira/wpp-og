# 🚀 Comandos para Implementar as Melhorias

## 📋 Checklist de Implementação

### ✅ **1. Parar Serviços Atuais**
```bash
# Parar workers Celery atuais
sudo supervisorctl stop celery-worker
sudo supervisorctl stop celery-beat

# Ou se usando Docker
docker-compose down
```

### ✅ **2. Atualizar Dependências**
```bash
cd whatsapp_backend
pip install -r requirements.txt

# Adicionar novas dependências se necessário
pip install redis==5.0.1 requests==2.31.0
```

### ✅ **3. Aplicar Migrações (se houver)**
```bash
python manage.py makemigrations
python manage.py migrate
```

### ✅ **4. Configurar Filas no Redis**
```bash
# Verificar se Redis está rodando
redis-cli ping

# Limpar filas antigas (opcional)
redis-cli FLUSHDB
```

### ✅ **5. Iniciar Novos Workers com Filas**
```bash
# Método 1: Workers separados por fila (RECOMENDADO)
celery -A whatsapp_backend worker -Q high_priority -c 4 --loglevel=info &
celery -A whatsapp_backend worker -Q normal -c 2 --loglevel=info &
celery -A whatsapp_backend worker -Q monitoring -c 1 --loglevel=info &
celery -A whatsapp_backend worker -Q maintenance -c 1 --loglevel=info &

# Método 2: Worker único para todas as filas (MAIS SIMPLES)
celery -A whatsapp_backend worker -l info --concurrency=8 &

# Beat scheduler
celery -A whatsapp_backend beat -l info &
```

### ✅ **6. Verificar se Tudo Está Funcionando**
```bash
# Testar webhook
curl -X POST http://localhost:8000/api/whatsapp/webhook/evolution/ \
     -H "Content-Type: application/json" \
     -d '{"test": "message"}'

# Verificar saúde do sistema
curl http://localhost:8000/api/whatsapp/monitoring/health/

# Ver filas ativas
curl http://localhost:8000/api/whatsapp/monitoring/queue-stats/
```

### ✅ **7. Configurar Monitoramento (Opcional)**
```bash
# Instalar Flower para interface web das filas
pip install flower
celery -A whatsapp_backend flower &

# Acesse: http://localhost:5555
```

---

## 🐳 **Para Deploy com Docker**

### ✅ **1. Atualizar docker-compose.yml**
```yaml
version: '3.8'

services:
  # ... outros serviços ...

  # Worker para filas de alta prioridade
  celery-high:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A whatsapp_backend worker -Q high_priority -c 4 -l info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - db

  # Worker para filas normais
  celery-normal:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A whatsapp_backend worker -Q normal,monitoring,maintenance -c 3 -l info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - db

  # Beat scheduler
  celery-beat:
    build:
      context: .
      dockerfile: Dockerfile.backend
    command: celery -A whatsapp_backend beat -l info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
    depends_on:
      - redis
      - db
```

### ✅ **2. Deploy**
```bash
# Build e start
docker-compose -f docker-compose.prod.yml up -d --build

# Verificar logs
docker-compose logs -f celery-high
docker-compose logs -f celery-normal
docker-compose logs -f celery-beat
```

---

## 🔧 **Comandos de Manutenção**

### **Monitoramento em Tempo Real**
```bash
# Ver status geral
curl http://localhost:8000/api/whatsapp/monitoring/health/ | jq

# Ver alertas
curl http://localhost:8000/api/whatsapp/monitoring/alerts/ | jq

# Ver métricas
curl http://localhost:8000/api/whatsapp/monitoring/metrics/ | jq

# Estatísticas das filas
curl http://localhost:8000/api/whatsapp/monitoring/queue-stats/ | jq
```

### **Reprocessar Mensagens Falhadas**
```bash
# Reprocessar últimas 24h
curl -X POST http://localhost:8000/api/whatsapp/monitoring/retry-failed/ \
     -H "Content-Type: application/json" \
     -d '{"hours": 24}' | jq

# Reprocessar última semana
curl -X POST http://localhost:8000/api/whatsapp/monitoring/retry-failed/ \
     -H "Content-Type: application/json" \
     -d '{"hours": 168}' | jq
```

### **Limpar Dados Antigos**
```bash
# Executar limpeza manual
python manage.py shell -c "
from whatsapp.tasks import cleanup_old_messages
cleanup_old_messages.delay()
"
```

### **Verificar Status de Tarefa Específica**
```bash
# Substituir TASK_ID pelo ID real da tarefa
curl http://localhost:8000/api/whatsapp/monitoring/task/TASK_ID/ | jq
```

---

## 📱 **Teste Completo do Sistema**

### ✅ **1. Teste de Envio Assíncrono**
```python
# No Django shell: python manage.py shell
from whatsapp.async_message_service import AsyncMessageService

async_service = AsyncMessageService()

# Teste simples
result = async_service.send_message_async(
    phone="5511999999999",
    message="Teste do sistema otimizado! 🚀",
    priority="normal"
)

print(f"Task ID: {result['task_id']}")
print(f"Status: {result['status']}")
```

### ✅ **2. Teste de Sistema de Fallback**
```python
# Simular falha para testar fallback
from whatsapp.fallback_service import FallbackService

fallback = FallbackService()
result = fallback.handle_api_failure(
    phone="5511999999999",
    message="Teste de fallback",
    error=Exception("Simulação de erro")
)

print(f"Status: {result['status']}")
print(f"Tentativas: {len(result['fallback_attempts'])}")
```

### ✅ **3. Teste de Pool de Conexões**
```python
from whatsapp.connection_pool import get_evolution_client

client = get_evolution_client()
stats = client.get_pool_stats()
print(f"Pool stats: {stats}")
```

---

## 🚨 **Troubleshooting Comum**

### **Problema: Workers não iniciam**
```bash
# Verificar configuração
python manage.py shell -c "from django.conf import settings; print(settings.CELERY_BROKER_URL)"

# Testar conexão Redis
redis-cli -u $CELERY_BROKER_URL ping

# Ver logs detalhados
celery -A whatsapp_backend worker -l debug
```

### **Problema: Mensagens não são enviadas**
```bash
# Verificar filas
celery -A whatsapp_backend inspect active
celery -A whatsapp_backend inspect scheduled

# Verificar Evolution API
curl http://localhost:8000/api/whatsapp/monitoring/health/ | jq '.components.evolution_api'
```

### **Problema: Rate limit atingido**
```bash
# Ver contador atual
redis-cli GET whatsapp_rate_limit:Elo

# Resetar manualmente
redis-cli DEL whatsapp_rate_limit:Elo
```

### **Problema: Muitas mensagens na fila**
```bash
# Ver quantidade de tarefas ativas
celery -A whatsapp_backend inspect active_queues

# Purgar fila específica (CUIDADO!)
celery -A whatsapp_backend purge -Q high_priority
```

---

## 📊 **Verificações de Produção**

### ✅ **Checklist Final**
- [ ] Workers Celery rodando (4 filas)
- [ ] Beat scheduler ativo
- [ ] Redis conectado e responsivo
- [ ] Evolution API online
- [ ] Webhook respondendo em <200ms
- [ ] Taxa de sucesso > 95%
- [ ] Sistema de monitoramento ativo
- [ ] Alertas configurados
- [ ] Logs estruturados funcionando

### **Comando de Verificação Completa**
```bash
#!/bin/bash
echo "🔍 Verificando sistema WhatsApp otimizado..."

# 1. Verificar saúde geral
echo "📊 Status geral:"
curl -s http://localhost:8000/api/whatsapp/monitoring/health/ | jq '.overall_status'

# 2. Verificar filas
echo "📤 Filas ativas:"
curl -s http://localhost:8000/api/whatsapp/monitoring/queue-stats/ | jq '.active_tasks'

# 3. Verificar alertas
echo "🚨 Alertas:"
curl -s http://localhost:8000/api/whatsapp/monitoring/alerts/ | jq '.count'

# 4. Verificar Evolution API
echo "📱 Evolution API:"
curl -s http://localhost:8000/api/whatsapp/monitoring/health/ | jq '.components.evolution_api.status'

echo "✅ Verificação completa!"
```

---

**🎉 Pronto! Seu sistema WhatsApp está otimizado e pronto para produção!**

Salve estes comandos para futuras manutenções e monitoramento. 🚀 