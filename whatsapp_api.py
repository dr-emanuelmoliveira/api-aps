# -*- coding: utf-8 -*-
"""
API integrada para extração de telefones de CSV e envio automático de mensagens WhatsApp.
Combina extract-telefones.py + send_messages.py + railway_scheduler.py em uma API FastAPI.
Permite automação de tarefas via Railway com agendamento de execuções.
"""

import os
import json
from typing import List, Optional, Dict
from datetime import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from extract_telefones import extrair_telefones_para_json
from send_messages import WhatsAppMessageSender
from railway_scheduler import AgendadorTarefas, TarefaAgendada, criar_rotas_scheduler

# ============================================================================
# INICIALIZAÇÃO DA API
# ============================================================================

app = FastAPI(
    title="API WhatsApp Busca Ativa - Com Scheduler",
    description="Extrai telefones de CSV, envia mensagens em lote e agenda tarefas automáticas no Railway",
    version="2.0.0",
)

# Permitir CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar scheduler global
agendador = AgendadorTarefas()

# ============================================================================
# MODELOS PYDANTIC
# ============================================================================

class MensagemRequest(BaseModel):
    """Modelo para requisição de envio de mensagens"""
    template_mensagem: str
    adicionar_info_optout: bool = True
    comando_optout: str = "SAIR"
    arquivo_contatos: Optional[str] = "contacts.json"


class ExtrairTelefonesRequest(BaseModel):
    """Modelo para extração de telefones"""
    coluna_telefone: str = "Telefone Celular"
    incluir_nome: bool = True
    pais: str = "BR"
    arquivo_saida: str = "contacts.json"


class RespostaEnvio(BaseModel):
    """Modelo para resposta de envio"""
    status: str
    total_processado: int
    sucesso: int
    erros: int
    ignorados: int
    timestamp: str
    arquivo_log: str


# ============================================================================
# LIFECYCLE EVENTS
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Inicia o scheduler ao iniciar a API"""
    agendador.iniciar()
    print("🚀 API iniciada com Scheduler ativo")


@app.on_event("shutdown")
async def shutdown_event():
    """Para o scheduler ao desligar a API"""
    agendador.parar()
    print("⏹️  API desligada")


# ============================================================================
# ENDPOINTS PRINCIPAIS
# ============================================================================

@app.get("/")
async def raiz():
    """
    Informações gerais da API.
    
    Retorna lista de endpoints disponíveis e status da aplicação.
    """
    return {
        "api": "WhatsApp Busca Ativa - Com Scheduler",
        "versao": "2.0.0",
        "status": "ativo",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "extração": {
                "extrair_telefones": "POST /extrair-telefones",
            },
            "envio": {
                "enviar_mensagens": "POST /enviar-mensagens",
                "enviar_simples": "POST /enviar-mensagens-simples",
            },
            "logs": {
                "listar_logs": "GET /listar-logs",
                "listar_optouts": "GET /listar-optouts",
                "adicionar_optout": "POST /adicionar-optout",
                "remover_optout": "DELETE /remover-optout",
            },
            "scheduler": {
                "agendar_tarefa": "POST /scheduler/agendar",
                "listar_tarefas": "GET /scheduler/tarefas",
                "executar_agora": "POST /scheduler/executar/{tarefa_id}",
                "historico": "GET /scheduler/historico",
                "status": "GET /scheduler/status",
            },
            "status": {
                "status_geral": "GET /status",
            }
        }
    }


# ============================================================================
# ENDPOINTS DE EXTRAÇÃO
# ============================================================================

@app.post("/extrair-telefones")
async def extrair_telefones(
    arquivo: UploadFile = File(...),
    coluna_telefone: str = "Telefone Celular",
    incluir_nome: bool = True,
    pais: str = "BR",
    arquivo_saida: str = "contacts.json",
    apikey: str = Header(None)
):
    """
    Extrai telefones de um CSV e gera arquivo JSON para envio.
    
    **Parâmetros:**
    - arquivo: CSV com dados dos pacientes (obrigatório)
    - coluna_telefone: Nome da coluna com telefones (padrão: "Telefone Celular")
    - incluir_nome: Se deve incluir nome dos pacientes (padrão: true)
    - pais: Código do país (padrão: "BR" para Brasil)
    - arquivo_saida: Nome do arquivo JSON gerado (padrão: "contacts.json")
    - apikey: Chave de API (header)
    
    **Formatos de telefone aceitos:**
    - 5537984198778 (11 dígitos)
    - 5537999999 (será preenchido para 11 dígitos)
    - +55 37 98419-8778 (com formatação)
    
    **Exemplo de resposta (201):**
    ```json
    {
        "status": "sucesso",
        "total_extraido": 50,
        "total_valido": 48,
        "total_invalido": 2,
        "arquivo_gerado": "contacts.json",
        "exemplo_contatos": [
            {"nome": "João Silva", "telefone": "+5537984198778"}
        ]
    }
    ```
    """
    try:
        # Salvar arquivo temporário
        conteudo = await arquivo.read()
        arquivo_temp = f"temp_{arquivo.filename}"
        with open(arquivo_temp, 'wb') as f:
            f.write(conteudo)
        
        # Extrair telefones
        telefones, invalidos = extrair_telefones_para_json(
            arquivo_temp,
            coluna_telefone=coluna_telefone,
            arquivo_saida=arquivo_saida,
            incluir_nome=incluir_nome,
            pais=pais
        )
        
        # Limpar arquivo temporário
        os.remove(arquivo_temp)
        
        # Preparar exemplo de contatos
        exemplo = telefones[:5] if len(telefones) > 5 else telefones
        invalidos_exemplo = invalidos[:5] if len(invalidos) > 5 else invalidos
        
        return JSONResponse(status_code=201, content={
            "status": "sucesso",
            "total_extraido": len(telefones) + len(invalidos),
            "total_valido": len(telefones),
            "total_invalido": len(invalidos),
            "arquivo_gerado": arquivo_saida,
            "exemplo_contatos": exemplo,
            "invalidos_exemplo": [
                {"valor": v, "motivo": m} for v, m in invalidos_exemplo
            ],
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao extrair telefones: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE ENVIO
# ============================================================================

@app.post("/enviar-mensagens")
async def enviar_mensagens(
    request: MensagemRequest,
    apikey: str = Header(None)
):
    """
    Envia mensagens em lote para todos os contatos do arquivo JSON.
    
    **Parâmetros:**
    - template_mensagem: Template da mensagem com {nome} como placeholder (obrigatório)
    - adicionar_info_optout: Se deve adicionar instruções de opt-out (padrão: true)
    - comando_optout: Comando para desinscrever (padrão: "SAIR")
    - arquivo_contatos: Arquivo JSON com contatos (padrão: "contacts.json")
    - apikey: Chave de API (header)
    
    **Exemplo de requisição:**
    ```json
    {
        "template_mensagem": "Olá {nome}, sua consulta está marcada!",
        "adicionar_info_optout": true,
        "comando_optout": "SAIR",
        "arquivo_contatos": "contacts.json"
    }
    ```
    
    **Resposta (200):**
    ```json
    {
        "status": "concluído",
        "total_processado": 48,
        "sucesso": 46,
        "erros": 2,
        "ignorados": 0,
        "timestamp": "2026-09-02T14:30:00.123456",
        "arquivo_log": "message_log.json"
    }
    ```
    """
    try:
        # Verificar se arquivo de contatos existe
        if not os.path.exists(request.arquivo_contatos):
            raise HTTPException(
                status_code=404,
                detail=f"Arquivo de contatos '{request.arquivo_contatos}' não encontrado. "
                       f"Execute /extrair-telefones primeiro."
            )
        
        # Criar instância do enviador
        sender = WhatsAppMessageSender(
            contacts_file=request.arquivo_contatos,
            log_file="message_log.json",
            optout_file="optout.json"
        )
        
        # Processar e enviar mensagens
        sender.process_contacts(
            message_template=request.template_mensagem,
            add_optout_info=request.adicionar_info_optout,
            optout_command=request.comando_optout
        )
        
        # Carregar log para contar resultados
        with open("message_log.json", 'r', encoding='utf-8') as f:
            log_data = json.load(f)
        
        sucesso = sum(1 for e in log_data if e.get("status") == "success")
        erros = sum(1 for e in log_data if e.get("status") == "error")
        ignorados = sum(1 for e in log_data if e.get("status") == "skipped")
        
        return JSONResponse(status_code=200, content={
            "status": "concluído",
            "total_processado": len(log_data),
            "sucesso": sucesso,
            "erros": erros,
            "ignorados": ignorados,
            "timestamp": datetime.now().isoformat(),
            "arquivo_log": "message_log.json"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao enviar mensagens: {str(e)}"
        )


@app.post("/enviar-mensagens-simples")
async def enviar_mensagem_simples(
    numero: str,
    mensagem: str,
    apikey: str = Header(None)
):
    """
    Envia uma única mensagem para um número específico.
    
    **Parâmetros:**
    - numero: Número de telefone (formato: 55DDD9XXXXXXXX ou +55DDD9XXXXXXXX)
    - mensagem: Texto da mensagem (obrigatório)
    - apikey: Chave de API (header)
    
    **Exemplo:**
    ```
    POST /enviar-mensagens-simples?numero=5537984198778&mensagem=Olá%20João!
    ```
    
    **Resposta (200):**
    ```json
    {
        "status": "sucesso",
        "numero": "5537984198778",
        "message_id": "3EB09D351EABB2B9C591CE",
        "timestamp": "2026-09-02T14:30:00.123456"
    }
    ```
    """
    try:
        sender = WhatsAppMessageSender()
        result = sender.send_message(numero, "Contato", mensagem)
        
        if result["success"]:
            return JSONResponse(status_code=200, content={
                "status": "sucesso",
                "numero": numero,
                "message_id": result.get("message_id"),
                "timestamp": datetime.now().isoformat()
            })
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get("error", "Erro desconhecido")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao enviar mensagem: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE LOGS E OPT-OUT
# ============================================================================

@app.get("/listar-logs")
async def listar_logs():
    """
    Retorna o conteúdo do arquivo de log de mensagens.
    
    **Resposta (200):**
    ```json
    {
        "total": 48,
        "logs": [
            {
                "timestamp": "2026-09-02T14:30:00.123456",
                "nome": "João Silva",
                "numero": "5537984198778",
                "status": "success",
                "mensagem": "Mensagem enviada. ID: 3EB09D351EABB2B9C591CE"
            }
        ]
    }
    ```
    """
    try:
        if not os.path.exists("message_log.json"):
            return JSONResponse({"total": 0, "logs": []})
        
        with open("message_log.json", 'r', encoding='utf-8') as f:
            logs = json.load(f)
        
        return JSONResponse({
            "total": len(logs),
            "logs": logs
        })
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao ler logs: {str(e)}"
        )


@app.get("/listar-optouts")
async def listar_optouts():
    """
    Retorna a lista de números com opt-out (desincrição).
    
    **Resposta (200):**
    ```json
    {
        "total_optout": 3,
        "numeros": [
            {
                "numero": "5537984198778",
                "nome": "João Silva",
                "motivo": "Solicitado pelo usuário",
                "data_optout": "2026-09-02T14:30:00"
            }
        ]
    }
    ```
    """
    try:
        if not os.path.exists("optout.json"):
            return JSONResponse({"total_optout": 0, "numeros": []})
        
        with open("optout.json", 'r', encoding='utf-8') as f:
            optout_list = json.load(f)
        
        return JSONResponse({
            "total_optout": len(optout_list),
            "numeros": optout_list
        })
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao ler opt-outs: {str(e)}"
        )


@app.post("/adicionar-optout")
async def adicionar_optout(
    numero: str,
    nome: str = "",
    motivo: str = "Solicitado pelo usuário",
    apikey: str = Header(None)
):
    """
    Adiciona um número à lista de opt-out (desinscrição).
    
    **Parâmetros:**
    - numero: Número de telefone (obrigatório)
    - nome: Nome do contato (opcional)
    - motivo: Motivo do opt-out (padrão: "Solicitado pelo usuário")
    - apikey: Chave de API (header)
    
    **Resposta (200):**
    ```json
    {
        "status": "sucesso",
        "mensagem": "Número 5537984198778 adicionado à lista de opt-out"
    }
    ```
    """
    try:
        sender = WhatsAppMessageSender()
        sender.add_optout(numero, nome, motivo)
        
        return JSONResponse(status_code=200, content={
            "status": "sucesso",
            "mensagem": f"Número {numero} adicionado à lista de opt-out"
        })
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao adicionar opt-out: {str(e)}"
        )


@app.delete("/remover-optout")
async def remover_optout(
    numero: str,
    apikey: str = Header(None)
):
    """
    Remove um número da lista de opt-out.
    
    **Parâmetros:**
    - numero: Número de telefone (obrigatório)
    - apikey: Chave de API (header)
    
    **Resposta (200):**
    ```json
    {
        "status": "sucesso",
        "mensagem": "Número 5537984198778 removido da lista de opt-out"
    }
    ```
    """
    try:
        sender = WhatsAppMessageSender()
        sender.remove_optout(numero)
        
        return JSONResponse(status_code=200, content={
            "status": "sucesso",
            "mensagem": f"Número {numero} removido da lista de opt-out"
        })
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao remover opt-out: {str(e)}"
        )


# ============================================================================
# ENDPOINTS DE STATUS
# ============================================================================

@app.get("/status")
async def status():
    """
    Retorna o status geral da API e seus recursos.
    
    **Resposta (200):**
    ```json
    {
        "api_ativa": true,
        "timestamp": "2026-09-02T14:30:00.123456",
        "scheduler_ativo": true,
        "arquivos": {
            "contatos": true,
            "logs": true,
            "optouts": true,
            "tarefas_agendadas": true
        }
    }
    ```
    """
    return JSONResponse({
        "api_ativa": True,
        "timestamp": datetime.now().isoformat(),
        "scheduler_ativo": agendador.scheduler.running,
        "arquivos": {
            "contatos": os.path.exists("contacts.json"),
            "logs": os.path.exists("message_log.json"),
            "optouts": os.path.exists("optout.json"),
            "tarefas_agendadas": os.path.exists("tarefas_agendadas.json")
        }
    })


# ============================================================================
# INTEGRAÇÃO DO SCHEDULER
# ============================================================================

# Registrar rotas do scheduler
criar_rotas_scheduler(app, agendador)


# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
