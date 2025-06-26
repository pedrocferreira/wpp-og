#!/bin/bash

echo "=== Iniciando Backend Django ==="

# Aguardar banco de dados estar disponível
echo "Aguardando banco de dados..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "Banco de dados disponível!"

# Aguardar Redis estar disponível
echo "Aguardando Redis..."
while ! nc -z redis 6379; do
  sleep 0.1
done
echo "Redis disponível!"

# Executar migrações
echo "Executando migrações..."
python manage.py migrate --noinput

# Coletar arquivos estáticos
echo "Coletando arquivos estáticos..."
mkdir -p staticfiles media logs beat
chmod -R 755 staticfiles media logs beat 2>/dev/null || true
python manage.py collectstatic --noinput || echo "Aviso: Erro ao coletar arquivos estáticos"

# Criar superusuário se não existir
echo "Verificando superusuário..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superusuário criado: admin/admin123')
else:
    print('Superusuário já existe')
EOF

echo "=== Backend iniciado com sucesso ==="

# Executar comando passado como parâmetro
exec "$@" 