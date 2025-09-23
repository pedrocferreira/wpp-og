# 🔔 Sistema de Lembretes Personalizados - WhatsApp IA

## 📋 Resumo das Implementações

### 🎯 Objetivo
Implementar um sistema inteligente de lembretes personalizados onde o cliente pode solicitar notificações específicas como:
- "me avisa 2 horas antes"
- "me avisa 1 semana antes" 
- "lembra 1 dia antes"
- "avisa 30 minutos antes"

---

## 🚀 Funcionalidades Implementadas

### 1. **Detecção Inteligente de Pedidos** 🧠
O sistema detecta automaticamente quando o cliente pede lembretes personalizados:

**Padrões Suportados:**
- `me avisa X horas antes`
- `me avisa X dias antes`
- `me avisa X semanas antes`
- `me avisa X minutos antes`
- `avisa X horas antes`
- `lembra X dias antes`
- `me lembra X semanas antes`

**Exemplos:**
- ✅ "me avisa 2 horas antes"
- ✅ "lembra 1 dia antes"
- ✅ "avisa 30 minutos antes"
- ✅ "me lembra 1 semana antes"
- ❌ "oi, tudo bem?" (não detecta)
- ❌ "quero agendar" (não detecta)

### 2. **Criação Automática de Lembretes** ⏰
Quando detectado um pedido de lembrete:
1. **Busca a próxima consulta** do cliente
2. **Calcula o horário** do lembrete
3. **Cria o lembrete personalizado** no banco de dados
4. **Confirma ao cliente** que foi configurado

### 3. **Mensagens Personalizadas** 💬
Cada tipo de lembrete gera uma mensagem específica e humanizada:

**2 horas antes:**
```
Oi, [Nome]! ⏰

Sua consulta é daqui a 2 horas (às 14:00).

Já está se preparando pra vir? Se houver algum imprevisto, me avise o quanto antes!

Te esperamos aqui! 😊
```

**1 dia antes:**
```
Oi, [Nome]! 😊

Só lembrando que você tem consulta agendada amanhã, sábado (19/07/2025) às 14:00.

Se não puder vir, me avise com antecedência, tá? Assim posso reagendar pra outro horário que funcione melhor pra você!

Até amanhã! 💙
```

**1 semana antes:**
```
Oi, [Nome]! 📅

Só lembrando que você tem consulta agendada na próxima semana, sábado (19/07/2025) às 14:00.

Se não puder vir, me avise com antecedência, tá? Assim posso reagendar pra outro horário que funcione melhor pra você!

Até lá! 💙
```

### 4. **Integração com IA** 🤖
O sistema está integrado ao SmartAIService com **prioridade máxima**:

1. **PRIORIDADE 1**: Verifica se é pedido de lembrete personalizado
2. **PRIORIDADE 2**: Verifica se é pedido de cancelamento
3. **PRIORIDADE 3**: Verifica se é pergunta sobre consultas existentes
4. **PRIORIDADE 4**: Verifica se é pergunta sobre disponibilidade
5. **PRIORIDADE 5**: Verifica se é agendamento específico
6. **PRIORIDADE 6**: Usa GPT para outras respostas

### 5. **Sistema de Envio Automático** 📤
- **Tarefa Celery**: `send_custom_reminders` executa a cada 2 minutos
- **Verificação**: Busca lembretes pendentes e envia via WhatsApp
- **Registro**: Marca como enviado com timestamp

---

## 🛠️ Implementações Técnicas

### **Novos Modelos Criados:**

#### `CustomReminderRequest`
```python
class CustomReminderRequest(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE)
    request_text = models.TextField()  # "me avisa 2 horas antes"
    reminder_timing = models.CharField(max_length=100)  # "2 horas antes"
    scheduled_for = models.DateTimeField()
    message = models.TextField()  # Mensagem personalizada
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
```

#### `AppointmentReminder` (Melhorado)
```python
class AppointmentReminder(models.Model):
    # ... campos existentes ...
    custom_message = models.TextField(blank=True, null=True)
    custom_timing = models.CharField(max_length=100, blank=True, null=True)
```

### **Novos Serviços Criados:**

#### `ReminderService`
- `detect_reminder_request()`: Detecta pedidos de lembretes
- `create_custom_reminder()`: Cria lembretes personalizados
- `_generate_custom_reminder_message()`: Gera mensagens personalizadas
- `send_custom_reminders()`: Envia lembretes pendentes

### **Novas Tarefas Celery:**
```python
'send-custom-reminders': {
    'task': 'appointments.tasks.send_custom_reminders',
    'schedule': crontab(minute='*/2'),  # executa a cada 2 minutos
}
```

---

## 📊 Fluxo Completo

### **Exemplo de Conversa:**

```
Cliente: "oi, tudo bem?"
IA: "Oi! Tudo bom? 😊"

Cliente: "quero agendar amanha as 14h"
IA: "Perfeito! Deixa eu verificar se amanhã às 14:00 está livre... ⏳"
IA: "Oba! Consegui agendar! 🎉 Sua consulta está marcada para amanhã às 14:00."

Cliente: "me avisa 2 horas antes"
IA: "Perfeito! ✅ Configurei um lembrete personalizado para te avisar 2 horas antes da sua consulta. Sua consulta está marcada para amanhã às 14:00. Você receberá a notificação no horário certo! 😊"
```

### **Processo Interno:**
1. **Detecção**: Sistema identifica "me avisa 2 horas antes"
2. **Busca**: Encontra a próxima consulta do cliente
3. **Cálculo**: Calcula que o lembrete deve ser enviado às 12:00
4. **Criação**: Cria `CustomReminderRequest` e `AppointmentReminder`
5. **Confirmação**: Responde ao cliente confirmando a configuração
6. **Envio**: Às 12:00, sistema envia automaticamente o lembrete

---

## 🧪 Testes Implementados

### **Comando de Teste:**
```bash
# Teste completo
docker exec wpp-og-backend-1 python manage.py test_custom_reminders

# Teste com mensagem específica
docker exec wpp-og-backend-1 python manage.py test_custom_reminders --test-message "me avisa 1 hora antes"
```

### **Testes Incluídos:**
1. **Detecção de pedidos**: Testa todos os padrões suportados
2. **Criação de lembretes**: Testa criação no banco de dados
3. **Mensagens personalizadas**: Testa geração de mensagens
4. **Mensagem específica**: Testa uma mensagem específica

---

## 🎯 Benefícios

### **Para o Cliente:**
- ✅ **Controle total**: Pode escolher quando receber lembretes
- ✅ **Flexibilidade**: Desde 30 minutos até 1 semana antes
- ✅ **Personalização**: Mensagens específicas para cada timing
- ✅ **Conveniência**: Não precisa lembrar de pedir lembretes

### **Para a Clínica:**
- ✅ **Redução de faltas**: Lembretes personalizados aumentam comparecimento
- ✅ **Automatização**: Sistema funciona 24/7 sem intervenção manual
- ✅ **Satisfação**: Clientes mais satisfeitos com atendimento personalizado
- ✅ **Eficiência**: Menos tempo gasto com reagendamentos

---

## 🔧 Configuração e Manutenção

### **Monitoramento:**
- Logs detalhados de criação e envio de lembretes
- Registro de erros e sucessos
- Métricas de eficácia dos lembretes

### **Escalabilidade:**
- Sistema suporta múltiplos lembretes por consulta
- Processamento assíncrono via Celery
- Banco de dados otimizado para consultas frequentes

### **Segurança:**
- Validação de timing (não permite lembretes no passado)
- Verificação de existência de consultas
- Tratamento de erros robusto

---

## 🚀 Próximos Passos

### **Melhorias Futuras:**
1. **Lembretes por data específica**: "me avisa dia 15"
2. **Lembretes múltiplos**: "me avisa 1 dia e 2 horas antes"
3. **Lembretes recorrentes**: Para consultas de retorno
4. **Preferências salvas**: Lembrar preferências do cliente
5. **Estatísticas**: Dashboard de eficácia dos lembretes

### **Integrações:**
1. **Google Calendar**: Sincronizar lembretes personalizados
2. **Email**: Enviar lembretes também por email
3. **SMS**: Backup via SMS para casos críticos
4. **Push Notifications**: Para app mobile futuro

---

## ✅ Status Atual

**IMPLEMENTADO E FUNCIONANDO:**
- ✅ Detecção de pedidos de lembretes
- ✅ Criação automática de lembretes personalizados
- ✅ Mensagens personalizadas por tipo de timing
- ✅ Integração com SmartAIService
- ✅ Sistema de envio automático via Celery
- ✅ Testes completos
- ✅ Migrações de banco de dados
- ✅ Logs e monitoramento

**SISTEMA PRONTO PARA PRODUÇÃO! 🎉** 