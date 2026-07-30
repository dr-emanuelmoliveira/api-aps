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

    detect
