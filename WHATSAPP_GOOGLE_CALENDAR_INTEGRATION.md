# 🚀 Integração WhatsApp + Google Calendar

## 📋 Resumo da Implementação

A integração entre WhatsApp e Google Calendar foi implementada com sucesso, permitindo que clientes façam agendamentos automaticamente via mensagens do WhatsApp, com criação automática de eventos no Google Calendar da Dra. Elisa.

## 🔧 Como Funciona

### 1. **Recepção da Mensagem via WhatsApp**
- Cliente envia mensagem pelo WhatsApp
- Evolution API captura a mensagem via webhook
- Sistema processa a mensagem no `EvolutionService`

### 2. **Processamento de Linguagem Natural**
- `SmartAIService` analisa a mensagem usando `NaturalLanguageProcessor`
- Identifica intenção de agendamento
- Extrai data e hora específicas da mensagem

### 3. **Verificação de Disponibilidade**
- Verifica horários de funcionamento (Segunda-Sexta: 8h-12h e 14h-18h, Sábado: 8h-13h)
- Consulta Google Calendar para verificar conflitos
- Verifica agendamentos locais no banco de dados

### 4. **Criação do Agendamento**
- Cria registro no banco local (`Appointment`)
- Cria evento no Google Calendar automaticamente
- Salva ID do Google Calendar no agendamento local

### 5. **Resposta Personalizada**
- Envia confirmação via WhatsApp
- Mensagem humanizada e detalhada
- Inclui todas as informações do agendamento

## 📁 Arquivos Principais

### Backend - Serviços
- `whatsapp_backend/whatsapp/evolution_service.py` - Processa webhooks do WhatsApp
- `whatsapp_backend/whatsapp/smart_ai_service.py` - IA para processamento de mensagens
- `whatsapp_backend/whatsapp/natural_language_processor.py` - Extração de data/hora
- `whatsapp_backend/whatsapp/calendar_service.py` - Integração Google Calendar

### Modelos
- `whatsapp_backend/appointments/models.py` - Modelo `Appointment` com campo `google_calendar_event_id`
- `whatsapp_backend/core/models.py` - Credenciais Google Calendar

## 🎯 Exemplos de Uso

### ✅ Mensagens que Criam Agendamento Automaticamente:
```
"Oi! Quero agendar uma consulta para amanhã às 15h"
"Posso marcar para quinta-feira às 10h da manhã?"
"Gostaria de marcar consulta terça às 14h"
"Quero marcar para hoje às 16h"
```

### ⚠️ Mensagens que Pedem Esclarecimento:
```
"Preciso agendar uma consulta" (sem data/hora específica)
"Quanto custa a consulta?" (não é agendamento)
```

### ❌ Mensagens que São Rejeitadas:
```
"Tem como marcar domingo às 14h?" (domingo fechado)
"Posso agendar às 22h?" (fora do horário)
```

## 🔄 Fluxo Completo

1. **Cliente envia**: "Quero agendar para amanhã às 14h"
2. **Sistema processa**: Extrai data (amanhã) e hora (14h)
3. **Verifica**: Horário de funcionamento ✅ | Google Calendar livre ✅ | Banco local livre ✅
4. **Cria agendamento**: Banco local + Google Calendar
5. **Responde**: "Pronto! Agendamento confirmado para amanhã às 14:00..."

## 📊 Recursos Implementados

### ✅ Processamento de Linguagem Natural
- Identifica intenções de agendamento
- Extrai datas relativas ("amanhã", "quinta-feira")
- Extrai horários ("15h", "2 da tarde", "às 14:00")
- Valida horários de funcionamento

### ✅ Integração Google Calendar
- Verificação de disponibilidade em tempo real
- Criação automática de eventos
- Sincronização bidirecional (agendamento local ↔ Google Calendar)
- Configuração de lembretes automáticos

### ✅ Inteligência Artificial
- Respostas contextuais e humanizadas
- Sugestão de horários alternativos quando ocupado
- Respostas diferentes para cada situação
- Fallback para respostas programadas

### ✅ Validações
- Horário de funcionamento
- Disponibilidade no Google Calendar
- Disponibilidade no banco local
- Formato de data/hora válido

## 🎨 Exemplos de Respostas da IA

### Agendamento Confirmado:
```
✅ Pronto, Maria! Agendamento confirmado!

Sua consulta ficou marcada para amanhã às 14:00 da tarde.

📅 Data: Quarta-feira, 25/06/2025
⏰ Horário: 14:00
🏥 Dra. Elisa Munaretti

📝 Lembre-se:
• Chegue 15 min antes
• Traga documento com foto
• Valor: R$ 620,00

Te mando um lembrete um dia antes! 💛
```

### Horário Ocupado:
```
Ai, que pena! O horário das 14:00 amanhã já está ocupado...

Mas olha só, tenho esses horários livres amanhã:
• 15:00 da tarde
• 16:00 da tarde  
• 17:00 da tarde

Qual desses funciona melhor pra você?
```

### Horário Inválido:
```
Opa! Esse horário a gente não está atendendo...

Nossos horários são:
Segunda a sexta: 8h às 12h e das 14h às 18h
Sábado: 8h às 13h
Domingo: fechadinho pra descansar 😅

Pode escolher um horário dentro desses aí?
```

## 🛠️ Configuração Técnica

### Variáveis de Ambiente Necessárias:
```bash
# Google Calendar
GOOGLE_CALENDAR_CLIENT_ID=seu_client_id
GOOGLE_CALENDAR_CLIENT_SECRET=seu_client_secret
GOOGLE_CALENDAR_REDIRECT_URI=http://155.133.22.207:8000/api/google-calendar/callback/

# Evolution API  
EVOLUTION_API_URL=http://sua_evolution_api
EVOLUTION_INSTANCE_ID=sua_instancia

# OpenAI (opcional para IA avançada)
OPENAI_API_KEY=sua_chave_openai
```

### Banco de Dados:
- Modelo `Appointment` já inclui campo `google_calendar_event_id`
- Credenciais Google salvas em `GoogleCalendarCredentials`
- Mensagens WhatsApp salvas em `WhatsAppMessage`

## 🧪 Testes

Execute os scripts de teste para verificar a integração:

```bash
# Teste básico dos serviços
docker exec -it wpp-og-backend-1 python test_whatsapp_google_calendar.py

# Simulação completa de webhook
docker exec -it wpp-og-backend-1 python test_webhook_simulation.py
```

## 📈 Métricas de Sucesso

### ✅ Funcionalidades Testadas e Aprovadas:
- ✅ Recepção de mensagens via webhook
- ✅ Processamento de linguagem natural  
- ✅ Identificação de intenção de agendamento
- ✅ Extração de data/hora da mensagem
- ✅ Verificação de disponibilidade
- ✅ Criação de agendamento no banco local
- ✅ Criação de evento no Google Calendar
- ✅ Envio de resposta personalizada
- ✅ Validação de horários de funcionamento

## 🚀 Próximos Passos (Opcionais)

### Melhorias Possíveis:
1. **Cancelamento via WhatsApp**: "Quero cancelar minha consulta de amanhã"
2. **Reagendamento**: "Posso remarcar para outro dia?"
3. **Lembretes automáticos**: Celery + cron jobs
4. **Múltiplos profissionais**: Expandir para mais médicos
5. **Integração com pagamento**: PIX automático
6. **Dashboard analytics**: Métricas de agendamentos via WhatsApp

## 🎉 Conclusão

A integração WhatsApp + Google Calendar está **100% funcional** e pronta para uso em produção. O sistema consegue:

- ✅ Identificar quando um cliente quer agendar via WhatsApp
- ✅ Extrair automaticamente data e hora da mensagem
- ✅ Verificar disponibilidade no Google Calendar
- ✅ Criar agendamento tanto no banco quanto no Google Calendar
- ✅ Responder de forma humanizada e profissional
- ✅ Validar horários de funcionamento

**A IA consegue processar linguagem natural brasileira e criar agendamentos automaticamente no Google Calendar! 🚀** 