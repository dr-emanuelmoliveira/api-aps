# 🏥 API APS - Busca Ativa

Sistema de integração com WhatsApp para envio de mensagens em lote usando a Evolution API.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-latest-green)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

## 📋 Tabela de Conteúdos

- [Características](#-características)
- [Instalação](#-instalação)
- [Uso](#-uso)
- [API Endpoints](#-api-endpoints)
- [Deploy](#-deploy)
- [Configuração](#-configuração)
- [Troubleshooting](#-troubleshooting)

## ✨ Características

- ✅ **API FastAPI** moderna e documentada
- ✅ **Integração WhatsApp** via Evolution API
- ✅ **Envio em Lote** para múltiplos contatos
- ✅ **Validação de Números** brasileiros automática
- ✅ **Personalização** de mensagens
- ✅ **Registro de Logs** detalhado
- ✅ **Docker** pronto para produção
- ✅ **Deploy Railway** com CI/CD
- ✅ **Health Check** automático

## 🚀 Início Rápido

### Instalação Local

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/api-aps.git
cd api-aps

# Crie um ambiente virtual
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# ou
venv\Scripts\activate  # Windows

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite .env com seus valores

# Execute a aplicação
uvicorn api:app --reload
```

A API estará disponível em: `http://localhost:8000`

### Com Docker

```bash
# Build
docker build -t api-aps .

# Run
docker run -p 8000:8000 api-aps

# Ou com docker-compose
docker-compose -f docker-compose.dev.yml up
```

## 📖 Uso

### Enviar Mensagem Simples

```python
import requests

response = requests.post(
    "http://localhost:8000/message/sendText/modulo-buscaiativa",
    json={
        "number": "5537984198778",
        "textMessage": {"text": "Olá! Tudo bem?"},
        "delay": 100
    },
    headers={"apikey": "sua-api-key"}
)

print(response.json())
```

### Enviar Múltiplas Mensagens

```python
from send_messages import WhatsAppMessageSender

sender = WhatsAppMessageSender(
    contacts_file="contacts.json",
    log_file="message_log.json"
)

message_template = "Olá {nome}, bem-vindo!"
sender.process_contacts(message_template)
```

Ver [README_MESSAGES.md](README_MESSAGES.md) para mais detalhes.

## 🔌 API Endpoints

### Status da API

```http
GET /
```

Retorna o status da aplicação.

**Resposta:**
```json
{
  "status": "ok",
  "message": "API está funcionando"
}
```

### Enviar Mensagem de Texto

```http
POST /message/sendText/{instanceName}
```

**Headers:**
```
apikey: sua-api-key
Content-Type: application/json
```

**Body:**
```json
{
  "number": "5537984198778",
  "textMessage": {
    "text": "Sua mensagem aqui"
  },
  "delay": 100,
  "quoted": {},
  "linkPreview": false,
  "mentioned": []
}
```

**Resposta (201/200):**
```json
{
  "key": {
    "remoteJid": "5537984198778@s.whatsapp.net",
    "fromMe": true,
    "id": "3EB09D351EABB2B9C591CE"
  },
  "message": {
    "extendedTextMessage": {
      "text": "Sua mensagem aqui"
    }
  },
  "messageTimestamp": "1788320047",
  "status": "PENDING"
}
```

### Documentação Interativa

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

## 🚀 Deploy

### No Railway

1. Conecte seu repositório GitHub
2. Railway detectará automaticamente
3. Configure as variáveis de ambiente
4. Deploy automático em cada push

**Ver [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) para instruções detalhadas.**

### Variáveis de Ambiente

```env
# Evolution API
EVOLUTION_API_URL=http://localhost:8080
EVOLUTION_API_KEY=sua-api-key-aqui
INSTANCE_NAME=modulo-buscaiativa

# Aplicação
PORT=8000
PYTHONUNBUFFERED=1
LOG_LEVEL=INFO
```

## ⚙️ Configuração

### Estrutura de Arquivos

```
api-aps/
├── 📄 api.py                    ← API FastAPI
├── 📄 main.py                   ← Lógica principal
├── 📄 app.py                    ← Envio simples
├── 📄 send_messages.py          ← Envio em lote
├── 📄 requirements.txt          ← Dependências
├── 📄 Dockerfile                ← Build Docker
├── 📄 Procfile                  ← Configuração Railway
├── 📄 railway.toml              ← Config avançada
├── 📄 .railway.json             ← Config JSON
├── 📄 runtime.txt               ← Versão Python
├── 📄 .env.example              ← Exemplo .env
├── 📄 contacts.json             ← Contatos exemplo
├── 📁 .github/workflows/        ← CI/CD
└── 📄 README.md                 ← Este arquivo
```

### Customização

#### Mudar Template de Mensagem

Edite `send_messages.py`:

```python
message_template = "Olá {nome}, sua consulta está marcada!"
sender.process_contacts(message_template)
```

#### Adicionar Novos Endpoints

Edite `api.py`:

```python
@app.post("/custom/endpoint")
async def custom_endpoint(data: dict):
    # Sua lógica aqui
    return {"status": "ok"}
```

## 🐛 Troubleshooting

### Erro: "API Evolution não conecta"

```bash
# Verifique se a API está rodando
docker ps

# Verifique o logs do container
docker logs evolution_api

# Teste a conexão
curl http://localhost:8080/
```

### Erro: "Número inválido"

Números devem ter formato: `55` + `DDD (2 dígitos)` + `número (8-9 dígitos)`

```python
# ✅ Válido
5537984198778    # 13 dígitos
55379999999      # Será adicionado o 9

# ❌ Inválido
553798419877     # Muito curto
5537999999999    # Dígitos incorretos
```

### Erro: "ModuleNotFoundError"

```bash
# Instale as dependências
pip install -r requirements.txt

# Ou no Docker
docker build -t api-aps .
```

### Port já em uso

```bash
# Altere a porta
PORT=8001 uvicorn api:app --host 0.0.0.0 --port 8001

# Ou libere a porta
lsof -i :8000
kill -9 <PID>
```

## 📊 Monitoramento

### Logs da Aplicação

```bash
# Localmente
tail -f message_log.json

# Em Produção (Railway)
railway logs
```

### Health Check

```bash
# Teste o health check
curl -i http://localhost:8000/

# Esperado: HTTP 200
```

## 🔐 Segurança

- ✅ API key em variáveis de ambiente
- ✅ HTTPS automático no Railway
- ✅ Rate limiting (implementar)
- ✅ Validação de entrada
- ✅ Logging de ações

## 📚 Recursos

- [FastAPI Docs](https://fastapi.tiangolo.com)
- [Evolution API](https://github.com/EvolutionAPI/evolution-api)
- [Railway Docs](https://docs.railway.app)
- [Docker Docs](https://docs.docker.com)

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/NovaFeature`)
3. Commit suas mudanças (`git commit -m 'Adiciona NovaFeature'`)
4. Push para a branch (`git push origin feature/NovaFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Contato

- **Email:** seu.email@exemplo.com
- **GitHub:** [@seu-usuario](https://github.com/seu-usuario)
- **Issues:** [GitHub Issues](https://github.com/seu-usuario/api-aps/issues)

## 🙏 Agradecimentos

- [Evolution API](https://github.com/EvolutionAPI/evolution-api) - API WhatsApp
- [FastAPI](https://fastapi.tiangolo.com) - Framework Web
- [Railway](https://railway.app) - Platform de Deploy

---

**Última atualização:** 2026-09-02  
**Versão:** 1.0.0  
**Status:** ✅ Ativo
