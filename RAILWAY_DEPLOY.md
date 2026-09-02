# 🚀 Deploy no Railway

Guia completo para fazer deploy da aplicação no Railway.

## 📋 Pré-requisitos

- Conta no [Railway.app](https://railway.app)
- GitHub conectado ao Railway
- Este repositório no GitHub

## 🔧 Passo a Passo para Deploy

### 1. Preparar o Repositório

```bash
# Certifique-se de que todos os arquivos estão commitados
git add .
git commit -m "Preparar para deploy no Railway"
git push origin main
```

### 2. Conectar no Railway

1. Acesse [railway.app](https://railway.app)
2. Faça login com sua conta GitHub
3. Clique em **"New Project"**
4. Selecione **"Deploy from GitHub repo"**
5. Autorize o Railway a acessar seus repositórios
6. Selecione este repositório (`api-aps`)
7. Railway detectará automaticamente que é um projeto Python

### 3. Configurar Variáveis de Ambiente

Após criar o projeto:

1. Vá para **Project Settings**
2. Clique em **"Variables"**
3. Adicione as variáveis necessárias:

```
EVOLUTION_API_URL=http://seu-api-url:8080
EVOLUTION_API_KEY=seu-api-key-aqui
INSTANCE_NAME=modulo-buscaiativa
PYTHONUNBUFFERED=1
```

### 4. Deploy Automático

- Railway detectará alterações no GitHub automaticamente
- Cada push para `main` acionará um novo deploy
- Você pode acompanhar o progresso na dashboard

### 5. Verificar o Status

1. Na dashboard, clique no projeto
2. Vá para **"Deployments"**
3. Veja o status: ✅ Deployed, 🔄 Building, ou ❌ Failed

### 6. Obter a URL da Aplicação

A URL da sua aplicação aparecerá em:
- **Project → Domain**
- Exemplo: `https://seu-projeto.up.railway.app`

## 📁 Estrutura dos Arquivos de Deploy

```
api-aps/
├── Dockerfile              ← Docker image
├── Procfile               ← Definição do processo
├── railway.toml           ← Configuração Railway
├── .railway.json          ← Alternativa JSON
├── runtime.txt            ← Versão do Python
├── .env.example           ← Exemplo de variáveis
├── requirements.txt       ← Dependências Python
├── api.py                 ← API principal
├── main.py                ← Lógica da aplicação
├── app.py                 ← Envio de mensagens
├── send_messages.py       ← Módulo em lote
├── contacts.json          ← Contatos exemplo
├── .gitignore             ← Arquivos ignorados
└── README.md              ← Documentação
```

## 🔍 Monitorar a Aplicação

### Logs

Para ver os logs da aplicação:

```bash
# Via Railway CLI
railway logs

# Ou na dashboard: Deployments → Logs
```

### Métricas

Railway fornece em tempo real:
- CPU usage
- Memory usage
- Network I/O
- Error rate
- Response time

## ⚙️ Configurações Avançadas

### 1. Custom Domain

```bash
railway domain add seu-dominio.com.br
```

### 2. Variáveis por Ambiente

Crie arquivos `.env.production` para produção.

### 3. Health Check

Railway verifica automaticamente:
- Endpoint: `/` (GET)
- Intervalo: 10 segundos
- Timeout: 5 segundos

Se falhar 3 vezes consecutivas, a aplicação reinicia.

### 4. Auto-scaling

Railway pode escalar automaticamente baseado em:
- CPU usage
- Memory usage
- Request rate

Configure em **Project Settings → Auto-scaling**.

## 🐛 Solução de Problemas

### Build falha

**Erro:** `ModuleNotFoundError`
- Verifique se todas as dependências estão em `requirements.txt`
- Rode localmente: `pip install -r requirements.txt`

**Erro:** `python: command not found`
- Verifique `runtime.txt`
- Exemplo: `python-3.11.9`

### Aplicação não inicia

**Erro:** `Port already in use`
- Railway define `PORT` automaticamente
- Use `$PORT` em todas as configurações

**Erro:** `Connection refused`
- Verifique se a aplicação está acessível em `0.0.0.0`
- Dockerfile: `--host 0.0.0.0`

### API Evolution não conecta

- Verifique se `EVOLUTION_API_URL` está correto
- Certifique-se que a API é acessível da internet
- Adicione delay na reconexão

## 📊 Monitorar Custos

Railway oferece um plano gratuito:
- $5 de crédito por mês
- Ideal para aplicações pequenas
- Custos adicionais se exceder

Acompanhe em **Account → Usage**.

## 🔐 Segurança

### Boas Práticas

1. **Não commite `.env`**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Use variáveis seguras**
   - API keys sempre em variáveis
   - Nunca no código

3. **Atualize dependências**
   ```bash
   pip install --upgrade pip
   pip list --outdated
   ```

4. **Proteja secrets**
   - Use Railway Secrets para dados sensíveis
   - Não exponha em logs

## 🚀 Deployment Contínuo (CI/CD)

Railway inclui CI/CD automático:

1. Cada push dispara build
2. Testes rodam automaticamente
3. Deploy ocorre se tudo passar

Adicione testes em `.github/workflows/`:

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest
```

## 📚 Recursos Úteis

- [Railway Docs](https://docs.railway.app)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Python on Railway](https://docs.railway.app/guides/python)

## ✅ Checklist de Deploy

- [ ] Todos os arquivos commitados
- [ ] `requirements.txt` atualizado
- [ ] `.env` adicionado ao `.gitignore`
- [ ] Dockerfile testado localmente
- [ ] Variáveis de ambiente configuradas
- [ ] Health check funcionando
- [ ] Logs sendo monitorados
- [ ] Domínio configurado (opcional)
- [ ] HTTPS ativado (automático)
- [ ] Backups configurados

## 🎯 Próximos Passos

Após deploy:

1. Teste os endpoints da API
2. Monitore os logs
3. Configure alertas
4. Implemente auto-scaling se necessário
5. Considere adicionar cache (Redis)
6. Implemente rate limiting

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs: `railway logs`
2. Consulte a documentação do Railway
3. Abra uma issue no GitHub
4. Contate o suporte do Railway

---

**Última atualização:** 2026-09-02  
**Versão:** 1.0.0
