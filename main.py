#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
============================================================
 BUSCA IATIVA - MULTI-INDICADORES
 Código Unificado para Deploy (GitHub + Railway)
============================================================
"""

# ============================================================
# --- 1. IMPORTAÇÃO DE BIBLIOTECAS ---
# [CORREÇÃO #1] Removidos todos os imports do Google Colab
# ============================================================

import pandas as pd
import numpy as np
import os
import re
import joblib
import warnings
import logging
import unicodedata
from datetime import datetime, timedelta

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score

import matplotlib
matplotlib.use('Agg')  # [CORREÇÃO #7] Backend sem display para servidor
import matplotlib.pyplot as plt
import seaborn as sns

from flask import Flask, request, jsonify, send_file

warnings.filterwarnings('ignore')

# [CORREÇÃO #15] Logging estruturado para produção
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# [CORREÇÃO #8] Título corrigido (era "Cópia de Busca IAtiva...")
SYSTEM_TITLE = "Busca IAtiva - Multi-indicadores"
SYSTEM_VERSION = "2.0.0"

# ============================================================
# --- 2. CONFIGURAÇÃO DOS INDICADORES ---
# [CORREÇÃO #5] Dicionário INDICADORES unificado (estava 3x duplicado)
# ============================================================

INDICADORES = {
    "C2": {
        "nome": "Desenvolvimento Infantil",
        "num_boas_praticas": 6,
        "padroes_decisivos": ["penta", "pentavalente", "vac_penta", "vac_polio",
                              "vac_scr", "vac_pneumo"],
        "colunas_detectar": ["vac_penta", "vac_polio", "idade_meses", "qtd_antro"],
        "colunas_excluir": ["hemoglobina", "influenza", "glicada", "cito", "hpv", "mamo"],
        "colunas_csv": {
            "nome": ["Nome", "nome", "Paciente"],
            "microarea": ["Microárea", "Microarea", "microarea", "MA"],
            "data_nascimento": ["Data de nascimento", "Data Nascimento",
                                "Data de Nascimento", "DtNascimento", "Data Nasc",
                                "Nascimento"],
            "idade_meses": ["Idade em meses", "idade_meses", "Idade_meses"],
            "qtd_atend_30d": ["Qtd atendimentos 30d", "qtd_atend_30d",
                              "Quantidade de atendimentos nos primeiros 30 dias"],
            "qtd_consultas": ["Qtd consultas", "qtd_consultas", "Quantidade de consultas"],
            "qtd_antro": ["Qtd antropometrias", "qtd_antro",
                          "Quantidade de antropometrias"],
            "data_antro": ["Data da última medição de peso e altura",
                           "data_antro", "Data antropometria"],
            "qtd_visitas": ["Qtd visitas domiciliares", "qtd_visitas",
                            "Quantidade de visitas domiciliares"],
            "vac_penta": ["Vacina penta", "vac_penta", "Pentavalente"],
            "vac_polio": ["Vacina polio", "vac_polio", "Polio"],
            "vac_scr": ["Vacina SCR", "vac_scr", "SCR"],
            "vac_pneumo": ["Vacina pneumo", "vac_pneumo", "Pneumocócica"],
        },
        # [CORREÇÃO #2] Corrigido: 3="GRAVE", 4="MUITO GRAVE" (estava duplicado)
        "niveis_prioridade": {
            0: "EM DIA", 1: "MODERADO", 2: "GRAVE",
            3: "MUITO GRAVE", 4: "CRÍTICO", 5: "CRÍTICO", 6: "CRÍTICO"
        },
        "max_prioridade": 6,
    },
    "C3": {
        "nome": "Gestação e Puerpério",
        "num_boas_praticas": 9,
        "padroes_decisivos": ["dtpa", "hiv", "sifilis", "hepatite",
                              "puerp", "prenatal", "gestacao"],
        "colunas_detectar": ["exame_hiv_1t", "data_dtpa", "data_consulta_puerp"],
        "colunas_excluir": ["hemoglobina", "glicada", "penta", "influenza"],
        "colunas_csv": {
            "nome": ["Nome", "nome", "Paciente"],
            "microarea": ["Microárea", "Microarea", "microarea"],
            "data_nascimento": ["Data de nascimento", "Data Nascimento"],
            "idade": ["Idade", "idade"],
            "qtd_atend_12sem": ["Qtd atend 12sem", "qtd_atend_12sem"],
            "qtd_consultas": ["Qtd consultas", "qtd_consultas"],
            "qtd_pa": ["Qtd PA", "qtd_pa", "Medicoes PA"],
            "qtd_antro": ["Qtd antropometrias", "qtd_antro"],
            "qtd_visitas": ["Qtd visitas domiciliares", "qtd_visitas"],
            "data_dtpa": ["Data dTpa", "data_dtpa", "Vacina dTpa"],
            "exame_hiv_1t": ["Exame HIV 1T", "exame_hiv_1t", "HIV primeiro trimestre"],
            "exame_sifilis_1t": ["Exame sifilis 1T", "exame_sifilis_1t"],
            "exame_hepb_1t": ["Exame hepB 1T", "exame_hepb_1t"],
            "exame_hepc_1t": ["Exame hepC 1T", "exame_hepc_1t"],
            "exame_hiv_3t": ["Exame HIV 3T", "exame_hiv_3t"],
            "exame_sifilis_3t": ["Exame sifilis 3T", "exame_sifilis_3t"],
            "data_consulta_puerp": ["Data consulta puerp", "data_consulta_puerp"],
            "data_visita_puerp": ["Data visita puerp", "data_visita_puerp"],
            "data_odonto": ["Data odonto", "data_odonto", "Atendimento odonto"],
        },
        "niveis_prioridade": {0: "EM DIA", 1: "MODERADO", 2: "GRAVE",
                              3: "MUITO GRAVE", 4: "CRÍTICO"},
        "max_prioridade": 4,
    },
    "C4": {
        "nome": "Diabetes Mellitus",
        "num_boas_praticas": 6,
        "padroes_decisivos": ["glicada", "hemoglobina", "hba1c",
                              "diabetes", "glicemia"],
        "colunas_detectar": ["data_hbglicada", "data_pes", "data_antro"],
        "colunas_excluir": ["penta", "influenza", "cito", "hpv", "mamo"],
        "colunas_csv": {
            "nome": ["Nome", "nome"],
            "microarea": ["Microárea", "Microarea"],
            "data_nascimento": ["Data de nascimento", "Data Nascimento"],
            "idade": ["Idade", "idade"],
            "data_consulta": ["Data última consulta", "data_consulta", "Ultima consulta"],
            "data_pa": ["Data PA", "data_pa", "Ultima PA"],
            "data_antro": ["Data antropometria", "data_antro"],
            "data_hbglicada": ["Data Hb glicada", "data_hbglicada", "HbA1c"],
            "data_pes": ["Data exame pés", "data_pes", "Exame pes"],
            "meses_visita": ["Meses desde visita", "meses_visita"],
            "dias_visita": ["Dias desde visita", "dias_visita"],
            "qtd_visitas": ["Qtd visitas", "qtd_visitas"],
        },
        "niveis_prioridade": {0: "EM DIA", 1: "MODERADO", 2: "GRAVE",
                              3: "MUITO GRAVE", 4: "CRÍTICO"},
        "max_prioridade": 4,
    },
    "C5": {
        "nome": "Hipertensão Arterial Sistêmica",
        "num_boas_praticas": 4,
        "padroes_decisivos": ["pressao", "pa ", "arterial", "hipertensao",
                              "sistolica", "diastolica"],
        "colunas_detectar": ["data_pa", "data_consulta", "data_antro"],
        "colunas_excluir": ["glicada", "hemoglobina", "penta", "influenza"],
        "colunas_csv": {
            "nome": ["Nome", "nome"],
            "microarea": ["Microárea", "Microarea"],
            "data_nascimento": ["Data de nascimento", "Data Nascimento"],
            "idade": ["Idade", "idade"],
            "data_consulta": ["Data última consulta", "data_consulta"],
            "data_pa": ["Data PA", "data_pa", "Ultima PA"],
            "data_antro": ["Data antropometria", "data_antro"],
            "meses_visita": ["Meses desde visita", "meses_visita"],
            "dias_visita": ["Dias desde visita", "dias_visita"],
            "qtd_visitas": ["Qtd visitas", "qtd_visitas"],
        },
        "niveis_prioridade": {0: "EM DIA", 1: "MODERADO", 2: "GRAVE",
                              3: "MUITO GRAVE", 4: "CRÍTICO"},
        "max_prioridade": 4,
    },
    "C6": {
        "nome": "Cuidado da Pessoa Idosa",
        "num_boas_praticas": 4,
        "padroes_decisivos": ["influenza", "idoso", "idade60", "maior60"],
        "colunas_detectar": ["data_influenza", "data_consulta", "data_antro"],
        "colunas_excluir": ["penta", "glicada", "cito", "hpv", "mamo"],
        "colunas_csv": {
            "nome": ["Nome", "nome"],
            "microarea": ["Microárea", "Microarea"],
            "data_nascimento": ["Data de nascimento", "Data Nascimento"],
            "idade": ["Idade", "idade"],
            "data_consulta": ["Data última consulta", "data_consulta"],
            "data_antro": ["Data antropometria", "data_antro"],
            "data_influenza": ["Data influenza", "data_influenza", "Vacina influenza"],
            "meses_visita": ["Meses desde visita", "meses_visita"],
            "dias_visita": ["Dias desde visita", "dias_visita"],
            "qtd_visitas": ["Qtd visitas", "qtd_visitas"],
        },
        "niveis_prioridade": {0: "EM DIA", 1: "MODERADO", 2: "GRAVE",
                              3: "MUITO GRAVE", 4: "CRÍTICO"},
        "max_prioridade": 4,
    },
    "C7": {
        "nome": "Prevenção do Câncer",
        "num_boas_praticas": 4,
        "padroes_decisivos": ["cito", "citopatologico", "hpv", "mamo",
                              "mamografia", "ssr", "rastreio"],
        "colunas_detectar": ["data_cito", "data_hpv", "data_mamo"],
        "colunas_excluir": ["penta", "influenza", "glicada", "hemoglobina"],
        "colunas_csv": {
            "nome": ["Nome", "nome"],
            "microarea": ["Microárea", "Microarea"],
            "data_nascimento": ["Data de nascimento", "Data Nascimento"],
            "idade": ["Idade", "idade"],
            "data_cito": ["Data citopatológico", "data_cito", "Citopatologico"],
            "data_hpv": ["Data HPV", "data_hpv"],
            "data_ssr": ["Data SSR", "data_ssr", "Rastreio SSR"],
            "data_mamo": ["Data mamografia", "data_mamo", "Mamografia"],
        },
        "niveis_prioridade": {0: "EM DIA", 1: "MODERADO", 2: "GRAVE",
                              3: "MUITO GRAVE", 4: "CRÍTICO"},
        "max_prioridade": 4,
    },
}

# Calendário vacinal C2
CALENDARIO_VACINAL_C2 = {
    "penta": {"doses_esperadas": 3, "idade_min": 2, "idade_max": 18},
    "polio": {"doses_esperadas": 3, "idade_min": 2, "idade_max": 18},
    "scr": {"doses_esperadas": 1, "idade_min": 12, "idade_max": 60},
    "pneumo": {"doses_esperadas": 3, "idade_min": 2, "idade_max": 24},
}

# ============================================================
# --- 3. FUNÇÕES AUXILIARES ---
# ============================================================

def _normalizar_texto(texto: str) -> str:
    """Remove acentos, converte para lowercase e strip."""
    if not isinstance(texto, str):
        return ""
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode('utf-8')
    return texto.lower().strip()

def _parse_data(valor) -> datetime:
    """Parse de data em múltiplos formatos."""
    if pd.isna(valor) or valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor
    formatos = [
        "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y/%m/%d",
        "%d/%m/%y", "%d.%m.%Y", "%Y-%m-%d %H:%M:%S"
    ]
    for fmt in formatos:
        try:
            return datetime.strptime(str(valor).strip(), fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(valor)
    except Exception:
        return None

def _extrair_meses(valor) -> float:
    """Extrai valor em meses de texto ou número."""
    if pd.isna(valor) or valor is None:
        return 0.0
    s = str(valor).lower().strip()
    m = re.search(r'(\d+(?:[.,]\d+)?)', s)
    if not m:
        return 0.0
    num = float(m.group(1).replace(',', '.'))
    if 'ano' in s:
        return num * 12
    return num

def _parse_idade(valor) -> int:
    """Parse de idade para inteiro."""
    if pd.isna(valor) or valor is None:
        return 0
    try:
        return int(float(str(valor).strip()))
    except (ValueError, TypeError):
        return 0

def _calcular_idade_data_nasc(data_nasc) -> int:
    """Calcula idade em anos a partir da data de nascimento."""
    if data_nasc is None:
        return 0
    dt = _parse_data(data_nasc)
    if dt is None:
        return 0
    hoje = datetime.now()
    idade = hoje.year - dt.year - ((hoje.month, hoje.day) < (dt.month, dt.day))
    return max(idade, 0)

# ============================================================
# --- 4. DETECÇÃO AUTOMÁTICA DO INDICADOR ---
# [CORREÇÃO #6] Função unificada (estava duplicada entre arquivos)
# ============================================================

def detectar_indicador(colunas_csv: list) -> str:
    """
    Detecta qual indicador (C2-C7) está presente no CSV
    baseado nos nomes das colunas.
    Sistema de scoring: +10 padrão decisivo, +1 coluna regular, -5 exclusão.
    """
    cols_norm = [_normalizar_texto(c) for c in colunas_csv]
    scores = {}

    for cod, info in INDICADORES.items():
        score = 0
        for padrao in info["padroes_decisivos"]:
            padrao_n = _normalizar_texto(padrao)
            if any(padrao_n in c for c in cols_norm):
                score += 10
        for col in info.get("colunas_detectar", []):
            col_n = _normalizar_texto(col)
            if any(col_n in c for c in cols_norm):
                score += 1
        for excl in info.get("colunas_excluir", []):
            excl_n = _normalizar_texto(excl)
            if any(excl_n in c for c in cols_norm):
                score -= 5
        scores[cod] = score

    detectado = max(scores, key=scores.get)
    logger.info(f"Indicador detectado: {detectado} (score={scores[detectado]})")
    return detectado if scores[detectado] > 0 else None

# ============================================================
# --- 4. CARREGAMENTO DO CSV ---
# [CORREÇÃO #1] Removido files.upload() do Google Colab
# [CORREÇÃO #9] Try/except robusto com detecção de encoding/delimitador
# ============================================================

def carregar_csv(caminho: str) -> pd.DataFrame:
    """Carrega CSV com detecção automática de encoding, delimitador e header."""
    encodings = ['utf-8', 'latin-1', 'cp1252']
    delimitadores = [';', ',', '\t']
    last_error = None

    for enc in encodings:
        for sep in delimitadores:
            try:
                df = pd.read_csv(caminho, sep=sep, encoding=enc, nrows=5)
                skip = 0
                cols_joined = _normalizar_texto(" ".join(df.columns.astype(str)))
                if "nome" not in cols_joined and "paciente" not in cols_joined:
                    skip = 1
                df = pd.read_csv(caminho, sep=sep, encoding=enc, skiprows=skip)
                logger.info(f"CSV carregado: {len(df)} linhas, encoding={enc}, sep='{sep}'")
                return df
            except Exception as e:
                last_error = e
                continue

    raise ValueError(f"Não foi possível ler o CSV. Último erro: {last_error}")

# ============================================================
# --- 5. PREPARAÇÃO DOS DADOS ---
# [CORREÇÃO #6] Função unificada (estava duplicada entre arquivos)
# ============================================================

def encontrar_coluna(df_colunas: list, candidatos: list) -> str:
    """Encontra a coluna do CSV que melhor corresponde aos candidatos."""
    df_cols_norm = {_normalizar_texto(c): c for c in df_colunas}
    for cand in candidatos:
        cand_n = _normalizar_texto(cand)
        for df_n, df_orig in df_cols_norm.items():
            if cand_n == df_n or cand_n in df_n:
                return df_orig
    return None

def preparar_dados(df: pd.DataFrame, codigo_indicador: str,
                   colunas_csv: dict) -> pd.DataFrame:
    """Mapeia colunas do CSV para nomes padronizados e calcula idade se necessário."""
    df_prep = df.copy()
    mapeamento = {}

    for chave_padrao, candidatos in colunas_csv.items():
        col_encontrada = encontrar_coluna(list(df.columns), candidatos)
        if col_encontrada:
            mapeamento[col_encontrada] = chave_padrao

    df_prep = df_prep.rename(columns=mapeamento)

    # Calcular idade se houver data_nascimento mas não idade
    if "data_nascimento" in df_prep.columns and "idade" not in df_prep.columns:
        df_prep["idade"] = df_prep["data_nascimento"].apply(_calcular_idade_data_nasc)

    # Calcular idade em meses para C2
    if codigo_indicador == "C2":
        if "data_nascimento" in df_prep.columns and "idade_meses" not in df_prep.columns:
            df_prep["idade_meses"] = df_prep["data_nascimento"].apply(
                lambda x: _calcular_idade_data_nasc(x) * 12
            )

    # Preencher NaNs numéricos com 0
    for col in df_prep.select_dtypes(include=[np.number]).columns:
        df_prep[col] = df_prep[col].fillna(0)

    logger.info(f"Dados preparados: {len(df_prep)} registros, {len(df_prep.columns)} colunas")
    return df_prep

# ============================================================
# --- 6. DEFINIÇÃO DAS BOAS PRÁTICAS POR INDICADOR ---
# [CORREÇÃO #6] Função unificada (estava duplicada entre arquivos)
# ============================================================

def definir_boas_praticas(codigo_indicador: str) -> list:
    """Retorna lista de critérios (boas práticas) para o indicador."""
    praticas = {
        "C2": [
            {"label": "Atendimento nos primeiros 30 dias", "chave": "qtd_atend_30d",
             "tipo": "minimo", "valor": 1},
            {"label": "Consultas regulares", "chave": "qtd_consultas",
             "tipo": "minimo", "valor": 3},
            {"label": "Antropometria", "chave": "qtd_antro",
             "tipo": "minimo", "valor": 1},
            {"label": "Visita domiciliar", "chave": "qtd_visitas",
             "tipo": "minimo", "valor": 1},
            {"label": "Vacinação básica (Penta)", "chave": "vac_penta",
             "tipo": "booleano", "valor": True},
            {"label": "Atualização antropométrica", "chave": "data_antro",
             "tipo": "recente", "dias": 180},
        ],
        "C3": [
            {"label": "Atendimento 1º trimestre", "chave": "qtd_atend_12sem",
             "tipo": "minimo", "valor": 1},
            {"label": "Consultas pré-natal", "chave": "qtd_consultas",
             "tipo": "minimo", "valor": 6},
            {"label": "Aferição de PA", "chave": "qtd_pa",
             "tipo": "minimo", "valor": 1},
            {"label": "Antropometria", "chave": "qtd_antro",
             "tipo": "minimo", "valor": 1},
            {"label": "Visita domiciliar", "chave": "qtd_visitas",
             "tipo": "minimo", "valor": 1},
            {"label": "Vacina dTpa", "chave": "data_dtpa",
             "tipo": "booleano", "valor": True},
            {"label": "Exame HIV 1º trimestre", "chave": "exame_hiv_1t",
             "tipo": "booleano", "valor": True},
            {"label": "Exame sífilis 1º trimestre", "chave": "exame_sifilis_1t",
             "tipo": "booleano", "valor": True},
            {"label": "Consulta puerpério", "chave": "data_consulta_puerp",
             "tipo": "booleano", "valor": True},
        ],
        "C4": [
            {"label": "Consulta médica", "chave": "data_consulta",
             "tipo": "recente", "dias": 120},
            {"label": "Aferição de PA", "chave": "data_pa",
             "tipo": "recente", "dias": 120},
            {"label": "Antropometria", "chave": "data_antro",
             "tipo": "recente", "dias": 180},
            {"label": "Hb glicada", "chave": "data_hbglicada",
             "tipo": "recente", "dias": 180},
            {"label": "Exame de pés", "chave": "data_pes",
             "tipo": "recente", "dias": 365},
            {"label": "Visita domiciliar", "chave": "qtd_visitas",
             "tipo": "minimo", "valor": 1},
        ],
        "C5": [
            {"label": "Consulta médica", "chave": "data_consulta",
             "tipo": "recente", "dias": 120},
            {"label": "Aferição de PA", "chave": "data_pa",
             "tipo": "recente", "dias": 90},
            {"label": "Antropometria", "chave": "data_antro",
             "tipo": "recente", "dias": 180},
            {"label": "Visita domiciliar", "chave": "qtd_visitas",
             "tipo": "minimo", "valor": 1},
        ],
        "C6": [
            {"label": "Consulta médica", "chave": "data_consulta",
             "tipo": "recente", "dias": 180},
            {"label": "Antropometria", "chave": "data_antro",
             "tipo": "recente", "dias": 365},
            {"label": "Vacina influenza", "chave": "data_influenza",
             "tipo": "recente", "dias": 365},
            {"label": "Visita domiciliar", "chave": "qtd_visitas",
             "tipo": "minimo", "valor": 1},
        ],
        "C7": [
            {"label": "Citopatológico", "chave": "data_cito",
             "tipo": "recente", "dias": 365},
            {"label": "HPV", "chave": "data_hpv",
             "tipo": "recente", "dias": 365},
            {"label": "SSR", "chave": "data_ssr",
             "tipo": "recente", "dias": 365},
            {"label": "Mamografia", "chave": "data_mamo",
             "tipo": "recente", "dias": 365},
        ],
    }
    return praticas.get(codigo_indicador, [])

def parse_doses_vacina(valor) -> int:
    """Extrai número de doses de vacina de texto."""
    if pd.isna(valor) or valor is None:
        return 0
    s = str(valor).lower().strip()
    if s in ("0", "", "nan", "none", "false"):
        return 0
    m = re.search(r'(\d+)', s)
    return int(m.group(1)) if m else (1 if s in ("sim", "true", "yes", "x") else 0)

def verificar_vacinas_c2(row, calendario: dict = CALENDARIO_VACINAL_C2) -> int:
    """Verifica status vacinal C2. Retorna número de vacinas em dia."""
    vacinas_ok = 0
    for vacina, config in calendario.items():
        col = f"vac_{vacina}"
        if col in row.index:
            doses = parse_doses_vacina(row[col])
            if doses >= config["doses_esperadas"]:
                vacinas_ok += 1
    return vacinas_ok

# ============================================================
# --- 7. VERIFICAÇÃO DE CRITÉRIOS ---
# [CORREÇÃO #3] Removida seção 7.1 duplicada
# [CORREÇÃO #4] Função _verificar_criterio_detalhado unificada (estava 2x)
# ============================================================

def _verificar_criterio_detalhado(row, criterio, codigo_indicador):
    """Verifica UM critério para UM paciente. Retorna (atende: bool, detalhe: str)."""
    chave = criterio["chave"]
    valor = row.get(chave, 0)
    tipo = criterio["tipo"]

    if tipo == "minimo":
        try:
            valor_num = float(valor) if valor is not None else 0
        except (ValueError, TypeError):
            valor_num = 0
        atende = valor_num >= criterio["valor"]
        detalhe = "OK" if atende else f"Faltam {int(criterio['valor'] - valor_num)}"

    elif tipo == "booleano":
        atende = bool(valor) and str(valor).strip().lower() not in ("0", "nan", "false", "")
        detalhe = "OK" if atende else "Pendente"

    elif tipo == "recente":
        dias_max = criterio.get("dias", 180)
        if valor is None or (isinstance(valor, str) and valor.strip() == ""):
            atende = False
            detalhe = "Sem registro"
        else:
            data = _parse_data(valor)
            if data is None:
                atende = False
                detalhe = "Data inválida"
            else:
                dias = (datetime.now() - data).days
                atende = dias <= dias_max
                detalhe = "OK" if atende else f"Último há {dias}d (limite {dias_max}d)"

    else:
        atende = True
        detalhe = "OK"

    return atende, detalhe

def verificar_criterios(df: pd.DataFrame, boas_praticas: list,
                        codigo_indicador: str) -> pd.DataFrame:
    """Aplica todos os critérios a todos os pacientes."""
    resultados = []

    for _, row in df.iterrows():
        atendidos = 0
        detalhes_lista = []

        for bp in boas_praticas:
            atende, det = _verificar_criterio_detalhado(row, bp, codigo_indicador)
            if atende:
                atendidos += 1
            detalhes_lista.append({"label": bp["label"], "atende": atende, "detalhe": det})

        total_bp = len(boas_praticas)
        completude = (atendidos / total_bp) * 100 if total_bp > 0 else 0
        faltantes = total_bp - atendidos
        max_pri = INDICADORES[codigo_indicador]["max_prioridade"]
        prioridade_idx = min(faltantes, max_pri)
        nivel = INDICADORES[codigo_indicador]["niveis_prioridade"].get(
            prioridade_idx, "CRÍTICO"
        )

        resultados.append({
            "completude": round(completude, 1),
            "qtd_faltante": faltantes,
            "nivel_prioridade": nivel,
            "prioridade_score": prioridade_idx,
            "detalhes": detalhes_lista,
        })

    df_result = df.copy()
    df_res = pd.DataFrame(resultados)
    for col in df_res.columns:
        df_result[col] = df_res[col].values

    logger.info(f"Critérios verificados para {len(df_result)} pacientes")
    return df_result

# ============================================================
# --- 8. GRÁFICOS EXPLORATÓRIOS ---
# [CORREÇÃO #7] Backend Agg para servidor
# [CORREÇÃO #13] Código ativo (estava comentado/morto)
# ============================================================

def gerar_grafico_pizza(df: pd.DataFrame, codigo_indicador: str) -> str:
    """Gera pie chart por microárea."""
    os.makedirs("static", exist_ok=True)
    if "microarea" not in df.columns:
        return None
    plt.figure(figsize=(8, 8))
    counts = df["microarea"].value_counts()
    plt.pie(counts.values, labels=counts.index, autopct='%1.1f%%', startangle=90)
    plt.title(f"Distribuição por Microárea - {INDICADORES[codigo_indicador]['nome']}")
    path = f"static/pizza_{codigo_indicador}.png"
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return path

def gerar_grafico_barras(df: pd.DataFrame, codigo_indicador: str) -> str:
    """Gera bar chart por nível de prioridade."""
    os.makedirs("static", exist_ok=True)
    if "nivel_prioridade" not in df.columns:
        return None
    ordem = ["EM DIA", "MODERADO", "GRAVE", "MUITO GRAVE", "CRÍTICO"]
    plt.figure(figsize=(10, 6))
    sns.countplot(data=df, x="nivel_prioridade", order=ordem, palette="viridis")
    plt.title(f"Distribuição por Prioridade - {INDICADORES[codigo_indicador]['nome']}")
    plt.xlabel("Nível de Prioridade")
    plt.ylabel("Quantidade de Pacientes")
    path = f"static/barras_{codigo_indicador}.png"
    plt.savefig(path, dpi=150, bbox_inches='tight')
    plt.close()
    return path

# ============================================================
# --- 9. ENGENHARIA DE FEATURES ---
# ============================================================

def criar_features_ml(df_resultado: pd.DataFrame, codigo_indicador: str):
    """Cria features numéricas para ML."""
    feature_cols = ["prioridade_score", "qtd_faltante", "completude"]
    if "idade" in df_resultado.columns:
        feature_cols.append("idade")
    elif "idade_meses" in df_resultado.columns:
        feature_cols.append("idade_meses")

    X = df_resultado[feature_cols].copy()

    # Encoding de microárea
    le_micro = LabelEncoder()
    if "microarea" in df_resultado.columns:
        X["microarea_enc"] = le_micro.fit_transform(
            df_resultado["microarea"].astype(str)
        )

    # Encoding de nível
    le_nivel = LabelEncoder()
    y_clf = le_nivel.fit_transform(df_resultado["nivel_prioridade"])

    # Target de regressão: dias até próxima consulta (estimado)
    y_reg = df_resultado["qtd_faltante"].values * 30  # estimativa: 30 dias por item faltante

    encoders = {"microarea": le_micro, "nivel": le_nivel}
    logger.info(f"Features criadas: {list(X.columns)}, {len(X)} amostras")
    return X, y_clf, y_reg, encoders

# ============================================================
# --- 10. TREINAMENTO DOS MODELOS ---
# ============================================================

def treinar_modelos(X, y_clf, y_reg):
    """Treina RandomForest para classificação e regressão."""
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_clf, test_size=0.2, random_state=42, stratify=y_clf    )

    clf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    clf.fit(X_train, y_train)
    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True)

    reg = RandomForestRegressor(n_estimators=100, random_state=42)
    reg.fit(X_train, y_reg[:len(X_train)] if len(y_reg) > len(X_train) else y_reg)

    logger.info(f"Modelo treinado: accuracy={accuracy:.2%}")
    return clf, reg, accuracy, report

# ============================================================
# --- 11. PREVISÃO DE DATAS DE CONSULTA ---
# ============================================================

def prever_consultas(clf, reg, X, df_resultado, codigo_indicador) -> pd.DataFrame:
    """Prediz dias até próxima consulta e data agendada."""
    dias_pred = reg.predict(X)
    data_base = datetime.now()

    resultado = df_resultado.copy()
    resultado["dias_ate_consulta"] = np.round(dias_pred).astype(int)
    resultado["data_agendada"] = resultado["dias_ate_consulta"].apply(
        lambda d: (data_base + timedelta(days=int(d))).strftime("%d/%m/%Y")
    )

    colunas_saida = ["data_agendada", "dias_ate_consulta"]
    if "nome" in resultado.columns:
        colunas_saida = ["nome"] + colunas_saida
    if "microarea" in resultado.columns:
        colunas_saida = ["nome", "microarea"] + colunas_saida[1:] if "nome" in colunas_saida else ["microarea"] + colunas_saida
    if "nivel_prioridade" in resultado.columns:
        colunas_saida = colunas_saida + ["nivel_prioridade"]
    if "qtd_faltante" in resultado.columns:
        colunas_saida = colunas_saida + ["qtd_faltante"]

    logger.info(f"Previsões geradas para {len(resultado)} pacientes")
    return resultado[colunas_saida]

# ============================================================
# --- 12. LISTA DE BUSCA ATIVA ---
# ============================================================

def gerar_lista_busca_ativa(df_resultado, codigo_indicador) -> pd.DataFrame:
    """Filtra pacientes que NÃO estão 'EM DIA', ordenados por prioridade."""
    ordem_prioridade = {"CRÍTICO": 0, "MUITO GRAVE": 1, "GRAVE": 2, "MODERADO": 3, "EM DIA": 4}

    df_filtrado = df_resultado[df_resultado["nivel_prioridade"] != "EM DIA"].copy()
    df_filtrado["ordem"] = df_filtrado["nivel_prioridade"].map(ordem_prioridade)
    df_filtrado = df_filtrado.sort_values("ordem").drop(columns=["ordem"])

    os.makedirs("output", exist_ok=True)
    path_csv = f"output/lista_busca_ativa_{codigo_indicador}.csv"
    df_filtrado.to_csv(path_csv, index=False, encoding='utf-8-sig')
    logger.info(f"Lista de busca ativa salva: {path_csv} ({len(df_filtrado)} pacientes)")

    # Log formatado com ícones
    icones = {"CRÍTICO": "🚨", "MUITO GRAVE": "🔴", "GRAVE": "🟠", "MODERADO": "🟡"}
    for _, row in df_filtrado.iterrows():
        nome = row.get("nome", "N/A")
        nivel = row.get("nivel_prioridade", "")
        icone = icones.get(nivel, "⚪")
        logger.info(f"  {icone} {nome} — {nivel}")

    return df_filtrado

# ============================================================
# --- 13. AGENDA DE CONSULTAS ---
# ============================================================

def gerar_agenda_consultas(df_previsao, codigo_indicador) -> pd.DataFrame:
    """Agrupa pacientes por data agendada, ordenados por prioridade."""
    if "data_agendada" not in df_previsao.columns:
        logger.warning("Coluna 'data_agendada' não encontrada para agenda")
        return pd.DataFrame()

    ordem_prioridade = {"CRÍTICO": 0, "MUITO GRAVE": 1, "GRAVE": 2, "MODERADO": 3, "EM DIA": 4}
    df_agenda = df_previsao.copy()
    if "nivel_prioridade" in df_agenda.columns:
        df_agenda["ordem"] = df_agenda["nivel_prioridade"].map(ordem_prioridade)
        df_agenda = df_agenda.sort_values(["data_agendada", "ordem"]).drop(columns=["ordem"])
    else:
        df_agenda = df_agenda.sort_values("data_agendada")

    os.makedirs("output", exist_ok=True)
    path_csv = f"output/agenda_consultas_{codigo_indicador}.csv"
    df_agenda.to_csv(path_csv, index=False, encoding='utf-8-sig')
    logger.info(f"Agenda salva: {path_csv}")

    # Resumo por dia
    for data, grupo in df_agenda.groupby("data_agendada"):
        logger.info(f"  📅 {data} — {len(grupo)} pacientes")

    return df_agenda

# ============================================================
# --- 14. RELATÓRIO DE COMPLETUDE ---
# ============================================================

def relatorio_completude(df_resultado, codigo_indicador) -> pd.DataFrame:
    """Agrupa por microárea e calcula métricas de completude."""
    if "microarea" not in df_resultado.columns:
        logger.warning("Coluna 'microarea' não encontrada para relatório")
        return pd.DataFrame()

    relatorio = df_resultado.groupby("microarea").agg(
        total_pacientes=("nome", "count"),
        completude_media=("completude", "mean"),
        criterios_faltantes_medios=("qtd_faltante", "mean"),
    ).reset_index()

    if "prioridade_score" in df_resultado.columns:
        relatorio["prioridade_media"] = df_resultado.groupby("microarea")["prioridade_score"].mean().values

    relatorio["completude_media"] = relatorio["completude_media"].round(1)
    relatorio["criterios_faltantes_medios"] = relatorio["criterios_faltantes_medios"].round(1)

    os.makedirs("output", exist_ok=True)
    path_csv = f"output/relatorio_completude_{codigo_indicador}.csv"
    relatorio.to_csv(path_csv, index=False, encoding='utf-8-sig')
    logger.info(f"Relatório de completude salvo: {path_csv}")

    return relatorio

# ============================================================
# --- 15. SALVAMENTO DO MODELO ---
# [CORREÇÃO #9] Try/except robusto
# ============================================================

def salvar_modelo(clf, reg, le_micro, le_nivel, codigo_indicador,
                  colunas_features, boas_praticas) -> str:
    """Salva modelo completo em .pkl com metadados."""
    try:
        os.makedirs("models", exist_ok=True)
        path = f"models/modelo_{codigo_indicador}_{datetime.now().strftime('%Y%m%d')}.pkl"

        modelo = {
            "clf": clf,
            "reg": reg,
            "le_micro": le_micro,
            "le_nivel": le_nivel,
            "colunas_features": colunas_features,
            "boas_praticas": boas_praticas,
            "metadados": {
                "indicador": codigo_indicador,
                "data_treinamento": datetime.now().isoformat(),
                "versao": SYSTEM_VERSION,
                "sistema": SYSTEM_TITLE,
            },
        }
        joblib.dump(modelo, path)
        logger.info(f"Modelo salvo: {path}")
        return path
    except Exception as e:
        logger.error(f"Erro ao salvar modelo: {e}")
        return None

# ============================================================
# --- 16. CARREGAR E USAR MODELO SALVO ---
# ============================================================

def carregar_e_usar_modelo(caminho_modelo: str, caminho_csv: str) -> dict:
    """Carrega modelo .pkl e aplica pipeline de predição em novo CSV."""
    try:
        modelo = joblib.load(caminho_modelo)
        clf = modelo["clf"]
        reg = modelo["reg"]
        codigo = modelo["metadados"]["indicador"]
        boas_praticas = modelo["boas_praticas"]

        df = carregar_csv(caminho_csv)
        df_prep = preparar_dados(df, codigo, INDICADORES[codigo]["colunas_csv"])
        df_result = verificar_criterios(df_prep, boas_praticas, codigo)
        X, y_clf, y_reg, encoders = criar_features_ml(df_result, codigo)
        df_previsao = prever_consultas(clf, reg, X, df_result, codigo)

        logger.info(f"Modelo carregado e aplicado: {caminho_modelo}")
        return {
            "indicador": codigo,
            "total_pacientes": len(df_result),
            "previsoes": df_previsao.to_dict(orient="records"),
        }
    except Exception as e:
        logger.error(f"Erro ao carregar/aplicar modelo: {e}")
        return {"error": str(e)}

# ============================================================
# --- 17. API FLASK (Railway) ---
# [CORREÇÃO #10] Wrapper Flask com endpoint /api/busca-ativa
# [CORREÇÃO #11] Endpoint /health para healthcheck
# [CORREÇÃO #14] Variável de ambiente PORT
# ============================================================

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health():
    """Healthcheck para Railway."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "sistema": SYSTEM_TITLE,
        "versao": SYSTEM_VERSION
    }), 200

@app.route('/api/detectar-indicador', methods=['POST'])
def api_detectar_indicador():
    """Detecta o indicador a partir das colunas do CSV."""
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    temp_path = "temp_upload.csv"
    file.save(temp_path)

    try:
        df = carregar_csv(temp_path)
        indicador = detectar_indicador(list(df.columns))
        if not indicador:
            return jsonify({"error": "Indicador não reconhecido"}), 400

        return jsonify({
            "indicador": indicador,
            "nome": INDICADORES[indicador]["nome"],
            "colunas_encontradas": list(df.columns),
            "total_linhas": len(df)
        }), 200
    except Exception as e:
        logger.error(f"Erro em /api/detectar-indicador: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/api/busca-ativa', methods=['POST'])
def api_busca_ativa():
    """Executa pipeline completo de busca ativa."""
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400

    file = request.files['file']
    temp_path = "temp_upload.csv"
    file.save(temp_path)

    try:
        # Pipeline completo
        df = carregar_csv(temp_path)
        indicador = detectar_indicador(list(df.columns))
        if not indicador:
            return jsonify({"error": "Indicador não reconhecido no CSV"}), 400

        colunas_csv = INDICADORES[indicador]["colunas_csv"]
        df_prep = preparar_dados(df, indicador, colunas_csv)
        boas_praticas = definir_boas_praticas(indicador)
        df_result = verificar_criterios(df_prep, boas_praticas, indicador)

        # Resumo para JSON
        colunas_saida = []
        for col in ["nome", "microarea", "nivel_prioridade", "completude", "qtd_faltante"]:
            if col in df_result.columns:
                colunas_saida.append(col)

        resumo = df_result[colunas_saida].to_dict(orient="records")

        # Estatísticas
        stats = {
            "total_pacientes": len(df_result),
            "em_dia": int((df_result["nivel_prioridade"] == "EM DIA").sum()),
            "moderado": int((df_result["nivel_prioridade"] == "MODERADO").sum()),
            "grave": int((df_result["nivel_prioridade"] == "GRAVE").sum()),
            "muito_grave": int((df_result["nivel_prioridade"] == "MUITO GRAVE").sum()),
            "critico": int((df_result["nivel_prioridade"] == "CRÍTICO").sum()),
            "completude_media": round(float(df_result["completude"].mean()), 1),
        }

        return jsonify({
            "indicador_detectado": indicador,
            "nome_indicador": INDICADORES[indicador]["nome"],
            "estatisticas": stats,
            "pacientes": resumo[:200],
        }), 200

    except Exception as e:
        logger.error(f"Erro em /api/busca-ativa: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/api/modelos', methods=['GET'])
def api_listar_modelos():
    """Lista modelos salvos."""
    modelos = []
    if os.path.exists("models"):
        for f in os.listdir("models"):
            if f.endswith(".pkl"):
                modelos.append({"arquivo": f, "caminho": f"models/{f}"})
    return jsonify({"modelos": modelos}), 200

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Requisição inválida", "detalhe": str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erro interno do servidor"}), 500

# ============================================================
# --- 18. FUNÇÃO MAIN E ENTRY POINT ---
# [CORREÇÃO #12] if __name__ guard
# ============================================================

def main(caminho_csv: str = None):
    """Pipeline completo: CSV → detecção → critérios → ML → relatórios."""
    if not caminho_csv:
        logger.error("Uso: python app.py <caminho_csv>")
        return

    logger.info(f"=== {SYSTEM_TITLE} v{SYSTEM_VERSION} ===")

    # 1. Carregar CSV
    df = carregar_csv(caminho_csv)
    logger.info(f"CSV carregado: {len(df)} registros")

    # 2. Detectar indicador
    indicador = detectar_indicador(list(df.columns))
    if not indicador:
        logger.error("Não foi possível detectar o indicador")
        return
    logger.info(f"Indicador detectado: {indicador} — {INDICADORES[indicador]['nome']}")

    # 3. Preparar dados
    colunas_csv = INDICADORES[indicador]["colunas_csv"]
    df_prep = preparar_dados(df, indicador, colunas_csv)

    # 4. Definir boas práticas
    boas_praticas = definir_boas_praticas(indicador)
    logger.info(f"Boas práticas: {len(boas_praticas)} critérios")

    # 5. Verificar critérios
    df_result = verificar_criterios(df_prep, boas_praticas, indicador)

    # 6. Gráficos
    gerar_grafico_pizza(df_result, indicador)
    gerar_grafico_barras(df_result, indicador)

    # 7. Features + Treinamento
    X, y_clf, y_reg, encoders = criar_features_ml(df_result, indicador)
    clf, reg, accuracy, report = treinar_modelos(X, y_clf, y_reg)
    logger.info(f"Acurácia: {accuracy:.2%}")

    # 8. Previsão
    df_previsao = prever_consultas(clf, reg, X, df_result, indicador)

    # 9. Lista de busca ativa
    df_busca = gerar_lista_busca_ativa(df_result, indicador)
    logger.info(f"Busca ativa: {len(df_busca)} pacientes fora do padrão")

    # 10. Agenda
    gerar_agenda_consultas(df_previsao, indicador)

    # 11. Relatório de completude
    relatorio = relatorio_completude(df_result, indicador)
    logger.info(f"Relatório: {len(relatorio)} microáreas")

    # 12. Salvar modelo
    salvar_modelo(
        clf, reg, encoders["microarea"], encoders["nivel"],
        indicador, list(X.columns), boas_praticas
    )

    logger.info("=== Pipeline concluído ===")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1].endswith('.csv'):
        # Modo CLI: python app.py dados.csv
        main(sys.argv[1])
    else:
        # Modo servidor (Railway/local)
        port = int(os.environ.get("PORT", 5000))
        logger.info(f"Iniciando {SYSTEM_TITLE} na porta {port}")
        app.run(host='0.0.0.0', port=port)
