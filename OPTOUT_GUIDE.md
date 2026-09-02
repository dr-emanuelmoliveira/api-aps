# 🔐 Sistema de Opt-Out

Documentação completa do sistema de opt-out para gerenciar consentimento e privacidade nos envios de mensagens WhatsApp.

## 📋 O que é Opt-Out?

**Opt-Out** é quando um usuário solicita que não receba mais mensagens. É essencial para:
- ✅ Respeitar a privacidade do usuário
- ✅ Cumprir regulamentações (LGPD, GDPR)
- ✅ Manter boa reputação
- ✅ Reduzir bloqueios de spam

## 🔄 Como Funciona

### 1. Mensagens Incluem Instruções de Opt-Out

Cada mensagem enviada inclui automaticamente:

```
Olá João, bem-vindo ao nosso serviço! 👋

📌 *Responda com 'SAIR'* para não receber mais mensagens.
```

### 2. Rastreamento de Opt-Out

Os números que solicitam opt-out são armazenados em `optout.json`:

```json
[
  {
    "numero": "5537984198778",
    "nome": "João Silva",
    "motivo": "Solicitado pelo usuário",
    "data_optout": "2026-09-02T10:30:45.123456"
  }
]
```

### 3. Verificação Automática

Antes de enviar, o sistema verifica se o número está em opt-out.

## 🚀 Como Usar

### Envio com Opt-Out Automático

```python
from send_messages import WhatsAppMessageSender

sender = WhatsAppMessageSender(
    contacts_file="contacts.json",
    log_file="message_log.json",
    optout_file="optout.json"
)

message = "Olá {nome}, bem-vindo!"

# Envia com opt-out automático
sender.process_contacts(
    message_template=message,
    add_optout_info=True,      # Adiciona instruções
    optout_command="SAIR"       # Comando para opt-out
)
```

**Resultado:**
- ✅ Números em opt-out são ignorados
- ✅ Instruções de opt-out adicionadas às mensagens
- ✅ Log salvo em `message_log.json`

### Gerenciar Opt-Outs via Menu

```bash
# Execute o gerenciador interativo
source venv/bin/activate
python3 manage_optout.py
```

**Menu de opções:**
```
1. Visualizar lista de opt-outs
2. Adicionar número a opt-out
3. Remover número de opt-out
4. Verificar se número está em opt-out
5. Limpar toda lista de opt-out
6. Importar opt-outs de arquivo CSV
7. Exportar opt-outs para CSV
0. Sair
```

### Gerenciar via Código

```python
from send_messages import WhatsAppMessageSender

sender = WhatsAppMessageSender()

# Adicionar opt-out
sender.add_optout(
    phone="5537984198778",
    nome="João Silva",
    motivo="Não quer mais receber"
)

# Remover opt-out
sender.remove_optout("5537984198778")

# Verificar se está em opt-out
if sender.is_opted_out("5537984198778"):
    print("Número está em opt-out")
else:
    print("Número pode receber mensagens")

# Ver estatísticas
stats = sender.get_optout_stats()
print(f"Total em opt-out: {stats['total_optout']}")
```

## 📊 Visualizando Dados de Opt-Out

### Ver Lista Completa

```bash
python3 manage_optout.py
# Escolha opção 1
```

Mostra:
- Número de telefone
- Nome
- Motivo do opt-out
- Data do opt-out

### Ver Estatísticas

```python
from send_messages import WhatsAppMessageSender

sender = WhatsAppMessageSender()
sender.print_optout_stats()
```

**Exemplo de output:**
```
============================================================
📋 ESTATÍSTICAS DE OPT-OUT
============================================================
Total de números em opt-out: 5

Motivos de opt-out:
  • Solicitado pelo usuário: 3
  • Número inválido: 1
  • Não quer mais receber: 1

Números:
  • 5537984198778 (João Silva) - 2026-09-02
  • 5537987654321 (Maria Santos) - 2026-09-01
  • 5537999999999 (Pedro Oliveira) - 2026-08-31
  • 5537988888888 (Ana Costa) - 2026-08-30
  • 5537977777777 (Carlos Silva) - 2026-08-29
============================================================
```

## 📁 Importar/Exportar Opt-Outs

### Importar de CSV

**Arquivo CSV esperado:**
```csv
numero,nome
5537984198778,João Silva
5537987654321,Maria Santos
```

**No menu:**
```
Opção 6: Importar opt-outs de arquivo CSV
Caminho do arquivo CSV: optout_lista.csv
✅ 2 números importados!
```

**Via código:**
```python
# Use a opção "Importar" no menu manage_optout.py
```

### Exportar para CSV

**No menu:**
```
Opção 7: Exportar opt-outs para CSV
Nome do arquivo de saída: meus_optouts.csv
✅ Exportado para meus_optouts.csv
```

**Arquivo gerado:**
```csv
numero,nome,motivo,data_optout
5537984198778,João Silva,Solicitado pelo usuário,2026-09-02T10:30:45.123456
5537987654321,Maria Santos,Não quer,2026-09-01T09:15:30.654321
```

## 🔍 Personalizar Comando de Opt-Out

O comando padrão é "SAIR", mas você pode personalizá-lo:

```python
sender.process_contacts(
    message_template="Olá {nome}!",
    add_optout_info=True,
    optout_command="REMOVER"  # Comando customizado
)
```

**Mensagem resultante:**
```
Olá João!

📌 *Responda com 'REMOVER'* para não receber mais mensagens.
```

### Múltiplas Opções de Opt-Out

Para envios complexos, você pode usar strings dinâmicas:

```python
template = """Olá {nome}, bem-vindo!

Para desistir:
• Responda "SAIR"
• Acesse: www.seusite.com/unsubscribe
• Clique no link no rodapé"""

sender.process_contacts(template, add_optout_info=False)
```

## 📊 Log de Opt-Outs

O arquivo `message_log.json` registra se um número foi:

```json
{
  "timestamp": "2026-09-02T10:30:45.123456",
  "nome": "João Silva",
  "numero": "5537984198778",
  "status": "skipped",
  "mensagem": "Número em lista de opt-out"
}
```

**Status possíveis:**
- `success` — Mensagem enviada
- `error` — Erro no envio
- `skipped` — Número em opt-out (ignorado)

## 🔒 Conformidade e Privacidade

### LGPD (Lei Geral de Proteção de Dados)

✅ Implementado:
- Rastreamento de consentimento
- Direito ao esquecimento (deletar opt-out)
- Logs de atividades
- Transparência nas mensagens

### GDPR (Regulação Europeia)

✅ Compatível com:
- Direito de acesso aos dados
- Direito de ser esquecido
- Direito de oposição
- Portabilidade de dados

### Boas Práticas

- ✅ Sempre incluir opção de opt-out
- ✅ Respeitar opt-outs imediatamente
- ✅ Manter logs de decisões
- ✅ Permitir re-optin se desejar
- ✅ Usar linguagem clara e simples

## 📈 Relatórios

### Resumo de Envio

Após cada envio, o sistema mostra:

```
📊 RESUMO DO ENVIO:
   ✅ Sucesso: 98/100
   ❌ Erros: 1/100
   ⏭️  Ignorados (opt-out): 1/100

📝 Log salvo em: message_log.json
📋 Opt-outs: 5 números
```

### Análise de Motivos

```
Motivos de opt-out:
  • Solicitado pelo usuário: 3
  • Número inválido: 1
  • Não quer mais receber: 1
```

## 🚀 Integração com Outras Ferramentas

### Exportar para Crm/Banco de Dados

```python
import csv
from send_messages import WhatsAppMessageSender

sender = WhatsAppMessageSender()

# Exporta opt-outs
with open('optout_export.csv', 'w') as f:
    writer = csv.DictWriter(f, fieldnames=['numero', 'nome', 'motivo', 'data'])
    writer.writeheader()
    for entry in sender.optout_list:
        writer.writerow({
            'numero': entry['numero'],
            'nome': entry['nome'],
            'motivo': entry['motivo'],
            'data': entry['data_optout'][:10]
        })
```

### Sincronizar com Banco de Dados

```python
# Exemplo com SQLite
import sqlite3
from send_messages import WhatsAppMessageSender

sender = WhatsAppMessageSender()
conn = sqlite3.connect('contactos.db')
cursor = conn.cursor()

for entry in sender.optout_list:
    cursor.execute(
        "UPDATE contactos SET optout=1 WHERE numero=?",
        (entry['numero'],)
    )

conn.commit()
conn.close()
```

## ⚠️ Troubleshooting

### Problema: Número continua recebendo mensagens

**Solução:**
```bash
# Verifique se está em opt-out
python3 manage_optout.py
# Escolha opção 4 e enter o número
```

### Problema: Opt-out não funciona

**Verifique:**
1. Arquivo `optout.json` existe?
2. Número formatado corretamente (55DDNNNNNNNNN)?
3. `add_optout_info=True` no `process_contacts()`?

### Problema: Importar não funciona

**Certifique-se que CSV tem:**
- Coluna `numero` (com 55 + DDN)
- Coluna `nome`
- Encoding UTF-8
- Não tem linhas em branco

## 📞 Suporte

Para dúvidas:
- Abra uma issue no GitHub
- Consulte `README.md`
- Verifique `RAILWAY_DEPLOY.md`

---

**Versão:** 1.0.0  
**Atualizado:** 2026-09-02
