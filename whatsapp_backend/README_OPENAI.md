# 🤖 Configuração do OpenAI para Respostas Inteligentes

## 📋 Pré-requisitos

1. **Conta no OpenAI**: Crie uma conta em [https://platform.openai.com](https://platform.openai.com)
2. **Créditos**: Adicione créditos à sua conta (o OpenAI oferece créditos gratuitos para novos usuários)
3. **Chave da API**: Gere uma chave da API

## 🔑 Como Obter a Chave da API

1. Acesse: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Faça login na sua conta OpenAI
3. Clique em **"Create new secret key"**
4. Dê um nome à sua chave (ex: "WhatsApp Bot")
5. Copie a chave gerada (começa com `sk-`)

⚠️ **IMPORTANTE**: Mantenha sua chave segura e não a compartilhe!

## ⚙️ Configuração Automática

### Opção 1: Script Automático (Recomendado)

```bash
cd /root/wpp-og/whatsapp_backend
python configure_openai.py
```

O script irá:
- Guiá-lo através do processo
- Validar a chave
- Salvar automaticamente no arquivo `.env`
- Testar a conexão

### Opção 2: Configuração Manual

1. Crie ou edite o arquivo `.env`:
```bash
cd /root/wpp-og/whatsapp_backend
nano .env
```

2. Adicione sua chave:
```env
OPENAI_API_KEY=sk-sua-chave-aqui
```

## 🧪 Testando a Configuração

```bash
cd /root/wpp-og/whatsapp_backend
python configure_openai.py test
```

## 🔄 Reiniciando o Servidor

Após configurar a chave, reinicie o servidor Django:

```bash
cd /root/wpp-og/whatsapp_backend
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

## 📊 Melhorias Implementadas

### ✅ Respostas Mais Inteligentes
- **Contexto de conversa**: O bot lembra do histórico da conversa
- **Personalidade definida**: Respostas consistentes e profissionais
- **Processamento de intenções**: Identifica o que o usuário quer
- **Respostas estruturadas**: Usa emojis e formatação para melhor UX

### ✅ Funcionalidades Avançadas
- **Agendamento inteligente**: Processa datas e horários
- **Confirmação de dados**: Sempre confirma antes de agendar
- **Tratamento de erros**: Respostas amigáveis em caso de problemas
- **Fallback para respostas mock**: Funciona mesmo sem OpenAI

### ✅ Configurações Otimizadas
- **Modelo GPT-3.5-turbo**: Equilibrio entre qualidade e custo
- **Temperature 0.7**: Respostas criativas mas consistentes
- **Max tokens 500**: Respostas completas mas concisas
- **Presence/Frequency penalty**: Evita repetições

## 💰 Custos

- **GPT-3.5-turbo**: ~$0.002 por 1K tokens
- **Conversa típica**: ~$0.01-0.05 por conversa
- **Uso moderado**: ~$5-20 por mês

## 🚨 Solução de Problemas

### Erro: "OpenAI API key não configurada"
- Verifique se a chave está no arquivo `.env`
- Confirme que a chave começa com `sk-`
- Reinicie o servidor Django

### Erro: "Rate limit exceeded"
- Aguarde alguns minutos
- Verifique seus créditos na conta OpenAI
- Considere usar um plano pago

### Erro: "Authentication failed"
- Verifique se a chave está correta
- Confirme se a conta tem créditos
- Teste a chave no site do OpenAI

## 📞 Suporte

Se precisar de ajuda:
1. Verifique os logs do Django
2. Teste a conexão com `python configure_openai.py test`
3. Consulte a documentação do OpenAI

---

**🎉 Com o OpenAI configurado, seu bot terá respostas muito mais inteligentes e naturais!** 