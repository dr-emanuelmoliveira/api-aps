# 📱 Módulo de Envio de Mensagens WhatsApp

Um módulo Python completo para enviar mensagens em lote via WhatsApp usando a Evolution API com validação, personalização e registro detalhado.

## 🚀 Características

- ✅ Envio em lote para múltiplos contatos
- ✅ Formatação automática de números (adiciona 9 se desatualizado)
- ✅ Personalização de mensagens com nome da pessoa
- ✅ Log detalhado de sucessos e erros
- ✅ Validação de números brasileiros
- ✅ Tratamento de erros e exceções
- ✅ Interface JSON para entrada/saída

## 📋 Pré-requisitos

```bash
# Certifique-se que você está no diretório do projeto
cd "/Users/Emanuel_Oliveira/Desktop/api-aps "

# Ative o ambiente virtual
source venv/bin/activate

# Instale as dependências
pip install requests pandas
```

## 🔧 Configuração

### 1. Preparar arquivo de contatos (contacts.json)

Crie um arquivo `contacts.json` com a estrutura:

```json
[
  {
    "nome": "João Silva",
    "numero": "5537984198778"
  },
  {
    "nome": "Maria Santos",
    "numero": "553799999999"
  },
  {
    "nome": "Pedro Oliveira",
    "numero": "55379988776655"
  }
]
```

**Formatos aceitos:**
- Com 9 dígitos no número: `5537984198778` (13 dígitos total)
- Com 8 dígitos (desatualizado): `553798419877` (12 dígitos total) ✅ O "9" será adicionado automaticamente

### 2. Configurar API Key

Abra o arquivo `send_messages.py` e atualize:

```python
API_KEY = "seu-api-key-aqui"
```

## 📝 Como Usar

### Modo Simples

```bash
# Ative o ambiente
source venv/bin/activate

# Execute o script
python3 send_messages.py
```

### Modo Programático

```python
from send_messages import WhatsAppMessageSender

# Crie uma instância
sender = WhatsAppMessageSender(
    contacts_file="contacts.json",
    log_file="message_log.json"
)

# Template com personalização
message_template = "Olá {nome}, bem-vindo ao nosso serviço! 👋"

# Envie as mensagens
sender.process_contacts(message_template)
```

### Exemplos de Templates

```python
# Simples
"Olá {nome}! Bem-vindo!"

# Profissional
"Prezado(a) {nome}, gostaríamos de informar que..."

# Consulta médica
"Olá {nome}, seu compromisso está marcado para amanhã às 14h."

# Sem personalização
"Bem-vindo ao nosso serviço!"
```

## 📊 Saída e Logs

Após a execução, você verá:

1. **Console**: Progresso em tempo real
   ```
   📱 Iniciando envio para 4 contatos...
   ============================================================
   
   [1/4] Enviando para João Silva...
   ✅ Sucesso! ID: 3EB0E3C3F3D4E2EABDA734
   
   [2/4] Enviando para Maria Santos...
   ❌ Erro: HTTP 400
   ```

2. **Arquivo message_log.json**: Registro detalhado
   ```json
   [
     {
       "timestamp": "2026-09-02T00:51:34.680056",
       "nome": "João Silva",
       "numero": "5537984198778",
       "status": "success",
       "mensagem": "Mensagem enviada. ID: 3EB0E3C3F3D4E2EABDA734"
     },
     {
       "timestamp": "2026-09-02T00:51:34.896391",
       "nome": "Maria Santos",
       "numero": "5537999999999",
       "status": "error",
       "mensagem": "HTTP 400"
     }
   ]
   ```

## 🔍 Validação de Números

O módulo valida automaticamente números brasileiros:

| Número | Status | Resultado |
|--------|--------|-----------|
| `5537984198778` | ✅ Válido | Enviado |
| `553798419877` | ✅ Válido | Adiciona "9": `5537984198778` |
| `55379999999` | ❌ Inválido | Muito curto (11 dígitos) |
| `553799999999999` | ❌ Inválido | Muito longo (15 dígitos) |
| `abc123456` | ❌ Inválido | Não contém apenas números |

## ⚙️ Personalização Avançada

### Modificar template de mensagem no código

Edite `send_messages.py`, na função `main()`:

```python
# Template simples
message_template = "Olá {nome}!"

# Template com emojis
message_template = "👋 Olá {nome}, bem-vindo ao nosso serviço!"

# Template multilinha
message_template = """
Prezado(a) {nome},

Gostaríamos de informar que...

Atenciosamente,
Equipe de Suporte
""".strip()
```

### Modificar delays entre mensagens

No arquivo `send_messages.py`, procure por:

```python
"delay": 100,  # Aumentar para enviar mais lentamente
```

- `100` = 100ms entre mensagens
- `1000` = 1 segundo entre mensagens
- `5000` = 5 segundos entre mensagens

## 🐛 Solução de Problemas

### "API indisponível"
- Verifique se Docker está rodando: `docker ps`
- Verifique se o container está ativo: `docker compose ps`

### "Número inválido"
- Certifique-se que tem o formato: `55` + `DDD (2 dígitos)` + `número (8 ou 9 dígitos)`
- Exemplo correto: `5537984198778` (13 dígitos)

### "HTTP 400"
- Número pode não estar registrado na plataforma
- Verifique a API key

### "Timeout - API não respondeu"
- A API está demorando muito
- Aumentar o `timeout` no código: `timeout=30`

## 📈 Estatísticas

Após cada envio, o módulo fornece:
- Total de contatos
- Quantidade de sucessos
- Quantidade de erros
- Arquivo de log completo com timestamps

## 🔐 Segurança

- A API key é armazenada no código (em produção, use variáveis de ambiente)
- Os logs contêm informações sensíveis - guarde-os com segurança
- Números de telefone são registrados nos logs

## 📝 Exemplos Completos

### Exemplo 1: Envio Simples
```bash
# Prepare o contacts.json
# Execute:
source venv/bin/activate && python3 send_messages.py
```

### Exemplo 2: Personalização de Mensagem
Edite o arquivo `send_messages.py`:
```python
message_template = "Olá {nome}, seu pedido foi aprovado! ✅"
sender.process_contacts(message_template)
```

### Exemplo 3: Múltiplos Envios
```bash
# Primeiro envio
python3 send_messages.py

# Modifique contacts.json com novos contatos

# Segundo envio
python3 send_messages.py
```

Os logs serão acumulados em `message_log.json`.

## 🚀 Próximos Passos

Você pode expandir este módulo com:
- [ ] Envio de imagens/mídia
- [ ] Agendamento de mensagens
- [ ] Integração com banco de dados
- [ ] Interface web para gerenciamento
- [ ] Estatísticas avançadas
- [ ] Suporte a templates HTML

---

**Criado em:** 2026-09-02  
**Versão:** 1.0.0
