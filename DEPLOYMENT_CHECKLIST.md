# ✅ Checklist de Deployment

Use este checklist para garantir que tudo está pronto para fazer deploy no Railway.

## 📋 Pré-Deploy Local

- [ ] Código testado localmente
- [ ] `python3 -m venv venv` criado
- [ ] Dependências instaladas: `pip install -r requirements.txt`
- [ ] `.env` configurado com valores corretos
- [ ] Aplicação inicia sem erros: `uvicorn api:app --reload`
- [ ] API responde em `http://localhost:8000`
- [ ] Documentação acessível em `http://localhost:8000/docs`
- [ ] Testes passam: `pytest test_api.py`

## 🐳 Testes com Docker

- [ ] Docker instalado e rodando
- [ ] Build funciona: `docker build -t api-aps .`
- [ ] Imagem inicia sem erros: `docker run -p 8000:8000 api-aps`
- [ ] Health check responde: `curl http://localhost:8000/`
- [ ] Docker-compose funciona: `docker-compose -f docker-compose.dev.yml up`

## 📦 Preparação do Repositório

### Arquivos Necessários

- [ ] `Dockerfile` ✅ Criado
- [ ] `Procfile` ✅ Criado
- [ ] `railway.toml` ✅ Criado
- [ ] `.railway.json` ✅ Criado
- [ ] `runtime.txt` ✅ Criado
- [ ] `requirements.txt` ✅ Atualizado
- [ ] `.env.example` ✅ Criado
- [ ] `README.md` ✅ Atualizado
- [ ] `RAILWAY_DEPLOY.md` ✅ Criado
- [ ] `.gitignore` ✅ Atualizado
- [ ] `.github/workflows/tests.yml` ✅ Criado

### Código

- [ ] Sem erros de sintaxe Python
- [ ] `python -m py_compile api.py` passa
- [ ] `python -m py_compile main.py` passa
- [ ] Sem prints para debug
- [ ] Sem dados sensíveis no código
- [ ] Sem caminhos hardcoded
- [ ] Variáveis de ambiente usadas corretamente

### Segurança

- [ ] `.env` está no `.gitignore`
- [ ] Nenhuma API key no código
- [ ] Nenhuma senha commited
- [ ] Tokens em variáveis de ambiente
- [ ] `.env.example` sem valores reais

### Git

- [ ] Repositório atualizado: `git status` limpo
- [ ] Todos os arquivos staged: `git add .`
- [ ] Commit feito: `git commit -m "Preparar para Railway"`
- [ ] Push realizado: `git push origin main`
- [ ] Branches atualizadas

## 🚀 Configuração no Railway

### Conta Railway

- [ ] Conta criada em [railway.app](https://railway.app)
- [ ] GitHub conectado
- [ ] Repositório visível

### Projeto Railway

- [ ] Novo projeto criado
- [ ] Repositório GitHub conectado
- [ ] Railway detectou Dockerfile
- [ ] Build iniciou automaticamente

### Variáveis de Ambiente

- [ ] `EVOLUTION_API_URL` configurada
- [ ] `EVOLUTION_API_KEY` configurada
- [ ] `INSTANCE_NAME` configurada
- [ ] `PYTHONUNBUFFERED=1` configurada
- [ ] `PORT` deixado como padrão (Railway configura)
- [ ] Nenhuma variável com valor de exemplo

### Domínio

- [ ] URL do Railway anotada
- [ ] Domínio customizado configurado (opcional)
- [ ] HTTPS ativado (automático)
- [ ] DNS propagado (se domínio customizado)

## 🔍 Verificação de Deploy

### Build

- [ ] Build completo sem erros
- [ ] Logs não mostram `ERROR`
- [ ] Tempo de build razoável (< 5 minutos)

### Aplicação

- [ ] Container está rodando
- [ ] Porta 8000 exposta
- [ ] Health check passando
- [ ] Nenhum restart infinito

### API

- [ ] Endpoint raiz responde: `GET /` → 200
- [ ] Documentação acessível: `/docs` → 200
- [ ] Endpoints funcionam (teste um)
- [ ] Logs visíveis em tempo real

## 📊 Monitoramento Pós-Deploy

### Logs

- [ ] Logs acessíveis em Railway dashboard
- [ ] Sem erros críticos nos logs
- [ ] Nenhuma exposição de dados sensíveis
- [ ] Timestamps corretos

### Performance

- [ ] Aplicação responde rapidamente (< 500ms)
- [ ] CPU usage baixo (< 50%)
- [ ] Memory usage aceitável (< 512MB)
- [ ] Sem memory leaks

### Health

- [ ] Health check passando
- [ ] Nenhum restart automático
- [ ] Uptime > 99%
- [ ] Nenhum erro 5xx

## 🔗 Testes Funcionais

### Mensagens

- [ ] Teste enviar mensagem simples
- [ ] Teste envio em lote
- [ ] Teste com número inválido
- [ ] Teste sem API key
- [ ] Log criado corretamente

### API

- [ ] Teste GET `/`
- [ ] Teste POST `/message/sendText/{instance}`
- [ ] Teste com headers incorretos
- [ ] Teste com payload inválido

### Documentação

- [ ] Swagger funciona: `/docs`
- [ ] ReDoc funciona: `/redoc`
- [ ] Endpoints documentados
- [ ] Exemplos de request/response

## 🔐 Segurança Final

- [ ] API key segura
- [ ] Sem dados sensíveis em logs
- [ ] HTTPS ativado
- [ ] CORS configurado (se necessário)
- [ ] Rate limiting considerado

## 📈 Próximos Passos

- [ ] Configurar alertas no Railway
- [ ] Configurar backups
- [ ] Documentar runbook de deploy
- [ ] Treinar equipe
- [ ] Monitoramento 24/7 setup

## 🚨 Rollback Plan

- [ ] Conhecer como reverter deploy
- [ ] Backup de database (se houver)
- [ ] Comunicação com usuários
- [ ] Teste de rollback em staging

## 📞 Contatos e Suporte

- [ ] Contatos de suporte documentados
- [ ] Escalation plan definido
- [ ] On-call schedule setup
- [ ] Alertas configurados

---

## ✨ Status de Deploy

| Item | Status |
|------|--------|
| Código | ✅ Pronto |
| Docker | ✅ Pronto |
| Git | ⏳ Aguardando push |
| Railway | ⏳ Aguardando deploy |
| Testes | ⏳ Aguardando verificação |
| Produção | ⏳ Offline |

## 🎯 Próxima Ação

1. Complete todas as verificações acima
2. Execute: `git push origin main`
3. Acesse [railway.app](https://railway.app)
4. Monitore o deployment

---

**Última atualização:** 2026-09-02  
**Responsável:** [Seu Nome]  
**Próxima revisão:** [Data]
