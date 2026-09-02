#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrai números de telefone da coluna "Telefone Celular" de um CSV e grava um JSON.
Formato padrão de saída: E.164 para Brasil (ex.: +55DD9XXXXXXXX).
"""

import pandas as pd
import re
import json
from typing import List, Tuple, Optional

def _normalizar_texto(texto):
    if not isinstance(texto, str):
        return ""
    texto = texto.lower().strip()
    texto = re.sub(r'[áàãâä]', 'a', texto)
    texto = re.sub(r'[éèêë]', 'e', texto)
    texto = re.sub(r'[íìîï]', 'i', texto)
    texto = re.sub(r'[óòõôö]', 'o', texto)
    texto = re.sub(r'[úùûü]', 'u', texto)
    texto = re.sub(r'[ç]', 'c', texto)
    texto = re.sub(r'[^a-z0-9\s]', '', texto)
    return ' '.join(texto.split())

def _carregar_csv_tolerante(caminho_csv: str) -> pd.DataFrame:
    encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    delims = [';', ',']
    last_exc = None
    for enc in encodings:
        for sep in delims:
            try:
                df = pd.read_csv(caminho_csv, sep=sep, encoding=enc, dtype=str, low_memory=False)
                # if dataframe has very few columns and sep was wrong, try other sep
                if df.shape[1] >= 2:
                    return df
                # otherwise keep trying
            except Exception as e:
                last_exc = e
                continue
    # fallback: attempt pandas auto-detect
    try:
        df = pd.read_csv(caminho_csv, dtype=str, low_memory=False)
        return df
    except Exception:
        raise ValueError(f"Não foi possível ler o CSV ({last_exc})")

def _achar_coluna(df: pd.DataFrame, nome_alvo: str) -> Optional[str]:
    nome_norm = _normalizar_texto(nome_alvo)
    col_map = { _normalizar_texto(c): c for c in df.columns }
    if nome_norm in col_map:
        return col_map[nome_norm]
    # tentativa por contenção
    for norm, orig in col_map.items():
        if nome_norm in norm or norm in nome_norm:
            return orig
    # heurística: procurar palavras-chave
    chave = _normalizar_texto(nome_alvo).split()
    for norm, orig in col_map.items():
        if any(k in norm for k in chave):
            return orig
    return None

def _limpar_telefone(raw: str, pais='BR') -> Optional[str]:
    if raw is None:
        return None
    s = str(raw).strip()
    if s == '' or s.lower() in ('nan', 'none'):
        return None
    # manter apenas dígitos
    digits = re.sub(r'\D', '', s)
    if digits == '':
        return None
    # remover prefixo internacional "00"
    if digits.startswith('00'):
        digits = digits[2:]
    # se começar com 55 (Brasil) e sobram > 11 dígitos, remover o 55 inicial
    if digits.startswith('55') and len(digits) > 11:
        digits = digits[2:]
    # remover zeros à esquerda indesejados
    digits = digits.lstrip('0')
    # tratar casos comuns:
    # - Brasil: 10 (AA + 8) ou 11 (AA + 9) dígitos
    # - se tiver mais que 11 dígitos, tentar pegar os últimos 11 (à vezes vem prefixos)
    if pais.upper() == 'BR':
        if len(digits) == 11 or len(digits) == 10:
            return '+55' + digits
        if len(digits) > 11:
            # assumir que os últimos 11 dígitos são DDD + número
            return '+55' + digits[-11:]
        # números curtos (9,8) sem DDD não são suficientes para envio automático (retornar None)
        return None
    else:
        # comportamento genérico: se tiver 8-15 dígitos, prefixar com + e devolver
        if 8 <= len(digits) <= 15:
            return '+' + digits
        return None

def extrair_telefones_para_json(caminho_csv: str,
                                coluna_telefone: str = "Telefone Celular",
                                arquivo_saida: str = "telefones.json",
                                incluir_nome: bool = False,
                                pais: str = "BR") -> Tuple[List[str], List[Tuple[str,str]]]:
    """
    Lê o CSV, extrai números da coluna especificada, valida/normaliza e salva JSON.
    Retorna (telefones_validos, invalidos) onde:
     - telefones_validos é lista de strings (E.164) ou lista de dicts se incluir_nome=True
     - invalidos é lista de tuplas (valor_original, motivo)
    """
    df = _carregar_csv_tolerante(caminho_csv)

    col_tel = _achar_coluna(df, coluna_telefone)
    if col_tel is None:
        raise ValueError(f"Coluna de telefone '{coluna_telefone}' não encontrada no CSV. Colunas disponíveis: {list(df.columns)[:20]}")

    nome_col = None
    # tentar achar coluna de nome se inclusión requerida
    if incluir_nome:
        nome_col = _achar_coluna(df, "Nome")
        if nome_col is None:
            incluir_nome = False  # não possível incluir nome

    vistos = set()
    lista_saida = []
    invalidos = []

    for _, row in df.iterrows():
        raw = row.get(col_tel, "")
        cleaned = _limpar_telefone(raw, pais=pais)
        if cleaned:
            if cleaned not in vistos:
                vistos.add(cleaned)
                if incluir_nome and nome_col:
                    nome = str(row.get(nome_col, "")).strip()
                    lista_saida.append({"nome": nome if nome else None, "telefone": cleaned})
                else:
                    lista_saida.append(cleaned)
        else:
            invalidos.append((str(raw), "formato inválido ou incompleto"))

    # escrever JSON
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump({"telefones": lista_saida}, f, ensure_ascii=False, indent=2)

    return lista_saida, invalidos

# Exemplo de uso:
# if __name__ == "__main__":
#     telefones, invalidos = extrair_telefones_para_json("dados.csv", incluir_nome=True)
#     print("Telefones válidos:", len(telefones))
#     print("Inválidos (exemplos):", invalidos[:10])
