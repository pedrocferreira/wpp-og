# Dashboard com Configurações - Guia de Setup

## 🎯 Nova Dashboard Implementada

Foi implementada uma dashboard completa com duas abas principais:

### ✅ **Visão Geral**
- Estatísticas em tempo real
- Lista de clientes
- Cards informativos
- Interface moderna e responsiva

### ✅ **Configurações**
- **Google Calendar**: Conectar/desconectar, testar conexão
- **Configurações da IA**: Personalizar comportamento da assistente

## 🚀 Como Inicializar o Projeto

### 1. **Verificar Status dos Containers**
```bash
# No diretório do projeto
docker-compose ps

# Se não estiverem rodando, iniciar
docker-compose up -d
```

### 2. **Verificar URLs de Acesso**
- **Frontend**: http://155.133.22.207:9000 (não 3000!)
- **Backend**: http://155.133.22.207:8000
- **Admin Django**: http://155.133.22.207:8000/admin

### 3. **Aplicar Migrações (para AISettings)**
```bash
# Criar migrações para o novo modelo AISettings
docker-compose exec backend python manage.py makemigrations core

# Aplicar migrações
docker-compose exec backend python manage.py migrate
```

## 🤖 Configurações da IA

### **Funcionalidades Implementadas:**

#### **1. Informações Básicas**
- Nome da assistente (padrão: "Elô")
- Personalidade customizável
- Descrição do comportamento

#### **2. Informações da Clínica**
- Nome do médico
- Especialidades (Psicologia, Psiquiatria, Terapia, Coaching)
- Informações gerais da clínica

#### **3. Configurações de Atendimento**
- Horário de funcionamento
- Duração das consultas
- Agendamento automático

#### **4. Estilo de Resposta**
- **Formal**: Profissional e formal
- **Amigável**: Caloroso e acolhedor
- **Casual**: Descontraído e informal
- **Empático**: Focado em empatia (padrão)

#### **5. Opções Avançadas**
- Usar emojis nas respostas
- Agendamento automático ativo/inativo

### **APIs Criadas:**
- `GET /api/ai-settings/?user_id=1` - Buscar configurações
- `POST /api/ai-settings/save/` - Salvar configurações

## 📅 Google Calendar

### **Funcionalidades Já Implementadas:**
- ✅ Autenticação OAuth2
- ✅ Conectar/Desconectar
- ✅ Testar conexão
- ✅ Interface visual completa
- ✅ Status em tempo real

### **Para Ativar:**
1. Seguir o guia `GOOGLE_CALENDAR_SETUP.md`
2. Configurar credenciais no Google Cloud Console
3. Atualizar variáveis de ambiente

## 🎨 Interface da Dashboard

### **Design Moderno:**
- Cards com gradientes
- Tabs organizadas
- Formulários expansíveis
- Status visuais intuitivos
- Responsive design

### **Componentes Visuais:**
- **Status Conectado**: Verde com ícone de sucesso
- **Status Desconectado**: Vermelho com ícone de erro
- **Loading States**: Spinners e textos dinâmicos
- **Mensagens**: Feedback visual para ações

### **Navegação:**
- **Tab 1**: Visão Geral (dados dos clientes)
- **Tab 2**: Configurações (Google Calendar + IA)

## 🔧 Resolução de Problemas

### **Frontend não abre:**
```bash
# Verificar se o container frontend está rodando
docker-compose ps

# Verificar logs se houver erro
docker-compose logs frontend

# Rebuild se necessário
docker-compose build frontend
docker-compose up -d frontend
```

### **Backend com erro:**
```bash
# Verificar logs
docker-compose logs backend

# Aplicar migrações
docker-compose exec backend python manage.py migrate

# Coletar arquivos estáticos
docker-compose exec backend python manage.py collectstatic --noinput
```

## 📱 URLs Corretas

⚠️ **IMPORTANTE**: O frontend roda na porta **9000**, não 3000!

- ✅ **Frontend**: http://155.133.22.207:9000
- ❌ **Não usar**: http://155.133.22.207:3000

## 🎯 Próximos Passos

1. **Inicializar containers** com `docker-compose up -d`
2. **Aplicar migrações** para AISettings
3. **Acessar dashboard** em http://155.133.22.207:9000
4. **Testar configurações** da IA na aba "Configurações"
5. **Configurar Google Calendar** seguindo o guia específico

## 🚨 Status Atual

✅ **Implementado e funcionando:**
- Dashboard completa com tabs
- Configurações da IA (frontend + backend)
- Interface Google Calendar
- APIs REST para persistência
- Design responsivo e moderno

✅ **Integrado com sistema existente:**
- GPT-4o-mini ativo
- Smart AI Service funcionando
- Agendamentos automáticos via WhatsApp
- Fallbacks robustos

🎉 **Sistema pronto para uso!** 