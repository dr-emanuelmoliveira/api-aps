# -*- coding: utf-8 -*-
"""
Scheduler para automatizar tarefas de extração e envio via Railway.
Permite agendar execuções de tarefas com interval ou cron-like patterns.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# ============================================================================
# MODELOS
# ============================================================================

class TarefaAgendada(BaseModel):
    """Modelo para agendamento de tarefas"""
    id: str
    nome: str
    tipo: str  # "extrair_telefones" ou "enviar_mensagens"
    ativo: bool = True
    horario: Optional[str] = None  # "14:30" para execução diária
    intervalo_minutos: Optional[int] = None  # Para executar a cada X minutos
    configuracao: Dict = {}  # Configurações específicas da tarefa
    proxima_execucao: Optional[str] = None
    ultima_execucao: Optional[str] = None
    status_ultima: Optional[str] = None


class ResultadoExecucao(BaseModel):
    """Resultado da execução de uma tarefa"""
    tarefa_id: str
    sucesso: bool
    timestamp: str
    mensagem: str
    detalhes: Dict = {}


# ============================================================================
# SCHEDULER
# ============================================================================

class AgendadorTarefas:
    """Gerenciador de tarefas agendadas para Railway"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.tarefas: Dict[str, TarefaAgendada] = {}
        self.historico_execucoes: List[ResultadoExecucao] = []
        self.carregar_tarefas()
    
    def iniciar(self):
        """Inicia o scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            print("✅ Scheduler iniciado")
    
    def parar(self):
        """Para o scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("⏹️  Scheduler parado")
    
    def carregar_tarefas(self):
        """Carrega tarefas do arquivo de configuração"""
        try:
            with open("tarefas_agendadas.json", 'r', encoding='utf-8') as f:
                dados = json.load(f)
                for tarefa_dict in dados.get("tarefas", []):
                    tarefa = TarefaAgendada(**tarefa_dict)
                    self.tarefas[tarefa.id] = tarefa
        except FileNotFoundError:
            self.tarefas = {}
    
    def salvar_tarefas(self):
        """Salva tarefas no arquivo de configuração"""
        with open("tarefas_agendadas.json", 'w', encoding='utf-8') as f:
            dados = {
                "tarefas": [
                    {
                        "id": t.id,
                        "nome": t.nome,
                        "tipo": t.tipo,
                        "ativo": t.ativo,
                        "horario": t.horario,
                        "intervalo_minutos": t.intervalo_minutos,
                        "configuracao": t.configuracao,
                        "proxima_execucao": t.proxima_execucao,
                        "ultima_execucao": t.ultima_execucao,
                        "status_ultima": t.status_ultima,
                    }
                    for t in self.tarefas.values()
                ]
            }
            json.dump(dados, f, ensure_ascii=False, indent=2)
    
    def agendar_tarefa(self, tarefa: TarefaAgendada) -> bool:
        """Agenda uma nova tarefa"""
        try:
            if not tarefa.ativo:
                return False
            
            self.tarefas[tarefa.id] = tarefa
            
            # Determinar tipo de agendamento
            if tarefa.horario:
                # Agendamento diário em horário fixo (ex: 14:30)
                hora, minuto = map(int, tarefa.horario.split(':'))
                self.scheduler.add_job(
                    self._executar_tarefa,
                    'cron',
                    hour=hora,
                    minute=minuto,
                    args=[tarefa.id],
                    id=tarefa.id,
                    replace_existing=True
                )
                print(f"✅ Tarefa '{tarefa.nome}' agendada para {tarefa.horario}")
            
            elif tarefa.intervalo_minutos:
                # Agendamento a cada X minutos
                self.scheduler.add_job(
                    self._executar_tarefa,
                    'interval',
                    minutes=tarefa.intervalo_minutos,
                    args=[tarefa.id],
                    id=tarefa.id,
                    replace_existing=True
                )
                print(f"✅ Tarefa '{tarefa.nome}' agendada a cada {tarefa.intervalo_minutos} minutos")
            
            self.salvar_tarefas()
            return True
        
        except Exception as e:
            print(f"❌ Erro ao agendar tarefa: {e}")
            return False
    
    def desagendar_tarefa(self, tarefa_id: str) -> bool:
        """Remove uma tarefa agendada"""
        try:
            self.scheduler.remove_job(tarefa_id)
            if tarefa_id in self.tarefas:
                del self.tarefas[tarefa_id]
            self.salvar_tarefas()
            return True
        except Exception as e:
            print(f"❌ Erro ao desagendar: {e}")
            return False
    
    def _executar_tarefa(self, tarefa_id: str):
        """Executa uma tarefa (callback interno)"""
        if tarefa_id not in self.tarefas:
            return
        
        tarefa = self.tarefas[tarefa_id]
        print(f"\n🔄 Executando tarefa: {tarefa.nome}")
        
        try:
            if tarefa.tipo == "extrair_telefones":
                resultado = self._executar_extracao(tarefa)
            elif tarefa.tipo == "enviar_mensagens":
                resultado = self._executar_envio(tarefa)
            else:
                resultado = ResultadoExecucao(
                    tarefa_id=tarefa_id,
                    sucesso=False,
                    timestamp=datetime.now().isoformat(),
                    mensagem="Tipo de tarefa desconhecido"
                )
            
            # Atualizar registro
            tarefa.ultima_execucao = resultado.timestamp
            tarefa.status_ultima = "sucesso" if resultado.sucesso else "erro"
            tarefa.proxima_execucao = self._calcular_proxima_execucao(tarefa).isoformat()
            
            self.historico_execucoes.append(resultado)
            self.salvar_tarefas()
            
            print(f"✅ Tarefa concluída: {resultado.mensagem}")
        
        except Exception as e:
            print(f"❌ Erro na execução: {e}")
            tarefa.status_ultima = "erro"
            self.salvar_tarefas()
    
    def _executar_extracao(self, tarefa: TarefaAgendada) -> ResultadoExecucao:
        """Executa tarefa de extração de telefones"""
        from extract_telefones import extrair_telefones_para_json
        
        config = tarefa.configuracao
        caminho_csv = config.get("caminho_csv", "dados.csv")
        
        try:
            telefones, invalidos = extrair_telefones_para_json(
                caminho_csv,
                coluna_telefone=config.get("coluna_telefone", "Telefone Celular"),
                arquivo_saida=config.get("arquivo_saida", "contacts.json"),
                incluir_nome=config.get("incluir_nome", True),
                pais=config.get("pais", "BR")
            )
            
            return ResultadoExecucao(
                tarefa_id=tarefa.id,
                sucesso=True,
                timestamp=datetime.now().isoformat(),
                mensagem=f"Extração concluída: {len(telefones)} contatos extraídos",
                detalhes={
                    "total_extraido": len(telefones),
                    "invalidos": len(invalidos),
                    "arquivo": config.get("arquivo_saida", "contacts.json")
                }
            )
        except Exception as e:
            return ResultadoExecucao(
                tarefa_id=tarefa.id,
                sucesso=False,
                timestamp=datetime.now().isoformat(),
                mensagem=f"Erro na extração: {str(e)}"
            )
    
    def _executar_envio(self, tarefa: TarefaAgendada) -> ResultadoExecucao:
        """Executa tarefa de envio de mensagens"""
        from send_messages import WhatsAppMessageSender
        
        config = tarefa.configuracao
        
        try:
            sender = WhatsAppMessageSender(
                contacts_file=config.get("arquivo_contatos", "contacts.json"),
                log_file=config.get("arquivo_log", "message_log.json")
            )
            
            sender.process_contacts(
                message_template=config.get("template_mensagem", "Olá {nome}!"),
                add_optout_info=config.get("adicionar_optout", True),
                optout_command=config.get("comando_optout", "SAIR")
            )
            
            # Ler resultados do log
            with open(config.get("arquivo_log", "message_log.json"), 'r') as f:
                logs = json.load(f)
            
            sucesso = sum(1 for e in logs if e.get("status") == "success")
            erros = sum(1 for e in logs if e.get("status") == "error")
            
            return ResultadoExecucao(
                tarefa_id=tarefa.id,
                sucesso=True,
                timestamp=datetime.now().isoformat(),
                mensagem=f"Envio concluído: {sucesso} sucessos, {erros} erros",
                detalhes={
                    "sucesso": sucesso,
                    "erros": erros,
                    "total": len(logs)
                }
            )
        except Exception as e:
            return ResultadoExecucao(
                tarefa_id=tarefa.id,
                sucesso=False,
                timestamp=datetime.now().isoformat(),
                mensagem=f"Erro no envio: {str(e)}"
            )
    
    def _calcular_proxima_execucao(self, tarefa: TarefaAgendada) -> datetime:
        """Calcula a próxima hora de execução"""
        agora = datetime.now()
        
        if tarefa.horario:
            hora, minuto = map(int, tarefa.horario.split(':'))
            proxima = agora.replace(hour=hora, minute=minuto, second=0)
            if proxima <= agora:
                proxima += timedelta(days=1)
            return proxima
        elif tarefa.intervalo_minutos:
            return agora + timedelta(minutes=tarefa.intervalo_minutos)
        
        return agora
    
    def listar_tarefas(self) -> List[TarefaAgendada]:
        """Lista todas as tarefas"""
        return list(self.tarefas.values())
    
    def obter_historico(self, tarefa_id: Optional[str] = None) -> List[ResultadoExecucao]:
        """Obtém histórico de execuções"""
        if tarefa_id:
            return [e for e in self.historico_execucoes if e.tarefa_id == tarefa_id]
        return self.historico_execucoes


# ============================================================================
# INTEGRAÇÃO COM FASTAPI
# ============================================================================

def criar_rotas_scheduler(app: FastAPI, agendador: AgendadorTarefas):
    """Cria rotas de scheduler na API"""
    
    @app.post("/scheduler/agendar")
    async def agendar_tarefa(tarefa: TarefaAgendada):
        """
        Agenda uma nova tarefa.
        
        **Exemplo - Extrair telefones diariamente às 8:00:**
        ```json
        {
            "id": "extracao_diaria",
            "nome": "Extração Diária de Telefones",
            "tipo": "extrair_telefones",
            "ativo": true,
            "horario": "08:00",
            "configuracao": {
                "caminho_csv": "dados.csv",
                "arquivo_saida": "contacts.json",
                "incluir_nome": true
            }
        }
        ```
        
        **Exemplo - Enviar mensagens a cada 2 horas:**
        ```json
        {
            "id": "envio_periodico",
            "nome": "Envio Periódico",
            "tipo": "enviar_mensagens",
            "ativo": true,
            "intervalo_minutos": 120,
            "configuracao": {
                "template_mensagem": "Olá {nome}, bem-vindo!",
                "adicionar_optout": true
            }
        }
        ```
        """
        if agendador.agendar_tarefa(tarefa):
            return {"status": "sucesso", "tarefa_id": tarefa.id}
        raise HTTPException(status_code=400, detail="Erro ao agendar tarefa")
    
    @app.get("/scheduler/tarefas")
    async def listar_tarefas():
        """Lista todas as tarefas agendadas"""
        return {"tarefas": agendador.listar_tarefas()}
    
    @app.get("/scheduler/tarefas/{tarefa_id}")
    async def obter_tarefa(tarefa_id: str):
        """Obtém detalhes de uma tarefa específica"""
        if tarefa_id in agendador.tarefas:
            return agendador.tarefas[tarefa_id]
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    @app.delete("/scheduler/tarefas/{tarefa_id}")
    async def desagendar_tarefa(tarefa_id: str):
        """Remove uma tarefa agendada"""
        if agendador.desagendar_tarefa(tarefa_id):
            return {"status": "sucesso", "mensagem": f"Tarefa {tarefa_id} removida"}
        raise HTTPException(status_code=404, detail="Tarefa não encontrada")
    
    @app.put("/scheduler/tarefas/{tarefa_id}")
    async def atualizar_tarefa(tarefa_id: str, tarefa: TarefaAgendada):
        """Atualiza uma tarefa agendada"""
        tarefa.id = tarefa_id  # Garantir ID correto
        if agendador.agendar_tarefa(tarefa):
            return {"status": "sucesso", "tarefa_id": tarefa_id}
        raise HTTPException(status_code=400, detail="Erro ao atualizar tarefa")
    
    @app.post("/scheduler/executar/{tarefa_id}")
    async def executar_agora(tarefa_id: str):
        """Executa uma tarefa imediatamente (sem aguardar agendamento)"""
        if tarefa_id not in agendador.tarefas:
            raise HTTPException(status_code=404, detail="Tarefa não encontrada")
        
        agendador._executar_tarefa(tarefa_id)
        return {"status": "sucesso", "mensagem": f"Tarefa {tarefa_id} executada"}
    
    @app.get("/scheduler/historico")
    async def obter_historico(tarefa_id: Optional[str] = None):
        """Obtém histórico de execuções"""
        return {
            "total": len(agendador.historico_execucoes),
            "historico": agendador.obter_historico(tarefa_id)
        }
    
    @app.get("/scheduler/status")
    async def status_scheduler():
        """Status do scheduler"""
        return {
            "rodando": agendador.scheduler.running,
            "total_tarefas": len(agendador.tarefas),
            "timestamp": datetime.now().isoformat()
        }
