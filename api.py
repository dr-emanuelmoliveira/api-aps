#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

 API FLASK — BUSCA IATIVA MULTI-INDICADORES
 Ponto de entrada para produção (gunicorn / Railway / Docker)

"""

import os
import logging
from flask import Flask, request, jsonify
from datetime import datetime

# Importar funções do módulo principal
from app import (
    SYSTEM_TITLE,
    SYSTEM_VERSION,
    INDICADORES,
    detectar_indicador,
    carregar_csv,
    preparar_dados,
    definir_boas_praticas,
    verificar_criterios,
    criar_features_ml,
    treinar_modelos,
    prever_consultas,
    gerar_lista_busca_ativa,
    gerar_agenda_consultas,
    relatorio_completude,
    salvar_modelo,
    gerar_grafico_pizza,
    gerar_grafico_barras,
    carregar_e_usar_modelo,
)

# Configuração de logging
logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Instância do Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB máximo

# 
# --- ENDPOINTS ---
# 

@app.route('/health', methods=['GET'])
def health():
    """Healthcheck para Railway."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "sistema": SYSTEM_TITLE,
        "versao": SYSTEM_VERSION
    }), 200

@app.route('/', methods=['GET'])
def index():
    """Página inicial com informações da API."""
    return jsonify({
        "sistema": SYSTEM_TITLE,
        "versao": SYSTEM_VERSION,
        "endpoints": {
            "GET /health": "Status do serviço",
            "POST /api/detectar-indicador": "Detecta indicador (C2-C7) do CSV",
            "POST /api/busca-ativa": "Pipeline completo de busca ativa",
            "POST /api/pipeline-completo": "Pipeline + ML + agenda + modelo",
            "GET /api/modelos": "Lista modelos salvos",
            "GET /api/indicadores": "Lista indicadores suportados"
        }
    }), 200

@app.route('/api/indicadores', methods=['GET'])
def listar_indicadores():
    """Lista todos os indicadores suportados."""
    lista = []
    for codigo, info in INDICADORES.items():
        lista.append({
            "codigo": codigo,
            "nome": info["nome"],
            "num_boas_praticas": info["num_boas_praticas"],
            "max_prioridade": info["max_prioridade"]
        })
    return jsonify({"indicadores": lista}), 200

@app.route('/api/detectar-indicador', methods=['POST'])
def api_detectar_indicador():
    """Detecta o indicador a partir das colunas do CSV enviado."""
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado. Use campo 'file' no multipart/form-data."}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "Arquivo sem nome."}), 400

    temp_path = "/tmp/temp_detect.csv"
    file.save(temp_path)

    try:
        df = carregar_csv(temp_path)
        indicador = detectar_indicador(list(df.columns))

        if not indicador:
            return jsonify({
                "error": "Indicador não reconhecido no CSV.",
                "colunas_encontradas": list(df.columns)
            }), 400

        return jsonify({
            "indicador": indicador,
            "nome": INDICADORES[indicador]["nome"],
            "colunas_csv": list(df.columns),
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
    """Executa pipeline de busca ativa: detecção + critérios + classificação."""
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado. Use campo 'file' no multipart/form-data."}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "Arquivo sem nome."}), 400

    temp_path = "/tmp/temp_busca.csv"
    file.save(temp_path)

    try:
        # 1. Carregar CSV
        df = carregar_csv(temp_path)

        # 2. Detectar indicador
        indicador = detectar_indicador(list(df.columns))
        if not indicador:
            return jsonify({"error": "Indicador não reconhecido no CSV."}), 400

        # 3. Preparar dados
        colunas_csv = INDICADORES[indicador]["colunas_csv"]
        df_prep = preparar_dados(df, indicador, colunas_csv)

        # 4. Verificar critérios
        boas_praticas = definir_boas_praticas(indicador)
        df_result = verificar_criterios(df_prep, boas_praticas, indicador)

        # 5. Estatísticas
        stats = {
            "total_pacientes": len(df_result),
            "em_dia": int((df_result["nivel_prioridade"] == "EM DIA").sum()),
            "moderado": int((df_result["nivel_prioridade"] == "MODERADO").sum()),
            "grave": int((df_result["nivel_prioridade"] == "GRAVE").sum()),
            "muito_grave": int((df_result["nivel_prioridade"] == "MUITO GRAVE").sum()),
            "critico": int((df_result["nivel_prioridade"] == "CRÍTICO").sum()),
            "completude_media": round(float(df_result["completude"].mean()), 1),
        }

        # 6. Resumo de pacientes (limitado a 200)
        colunas_saida = []
        for col in ["nome", "microarea", "nivel_prioridade", "completude", "qtd_faltante"]:
            if col in df_result.columns:
                colunas_saida.append(col)

        pacientes = df_result[colunas_saida].head(200).to_dict(orient="records")

        # 7. Lista de busca ativa
        df_busca = gerar_lista_busca_ativa(df_result, indicador)

        return jsonify({
            "indicador": indicador,
            "nome_indicador": INDICADORES[indicador]["nome"],
            "estatisticas": stats,
            "pacientes_busca_ativa": len(df_busca),
            "pacientes": pacientes,
        }), 200

    except Exception as e:
        logger.error(f"Erro em /api/busca-ativa: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/api/pipeline-completo', methods=['POST'])
def api_pipeline_completo():
    """Executa pipeline completo: CSV → critérios → ML → agenda → modelo salvo."""
    if 'file' not in request.files:
        return jsonify({"error": "Nenhum arquivo enviado. Use campo 'file' no multipart/form-data."}), 400

    file = request.files['file']
    if not file.filename:
        return jsonify({"error": "Arquivo sem nome."}), 400

    temp_path = "/tmp/temp_pipeline.csv"
    file.save(temp_path)

    try:
        # 1. Carregar e detectar
        df = carregar_csv(temp_path)
        indicador = detectar_indicador(list(df.columns))
        if not indicador:
            return jsonify({"error": "Indicador não reconhecido."}), 400

        # 2. Preparar e verificar
        colunas_csv = INDICADORES[indicador]["colunas_csv"]
        df_prep = preparar_dados(df, indicador, colunas_csv)
        boas_praticas = definir_boas_praticas(indicador)
        df_result = verificar_criterios(df_prep, boas_praticas, indicador)

        # 3. Gráficos
        gerar_grafico_pizza(df_result, indicador)
        gerar_grafico_barras(df_result, indicador)

        # 4. ML: Features + Treino
        X, y_clf, y_reg, encoders = criar_features_ml(df_result, indicador)
        clf, reg, accuracy, report = treinar_modelos(X, y_clf, y_reg)

        # 5. Previsão
        df_previsao = prever_consultas(clf, reg, X, df_result, indicador)

        # 6. Lista + Agenda + Relatório
        df_busca = gerar_lista_busca_ativa(df_result, indicador)
        gerar_agenda_consultas(df_previsao, indicador)
        relatorio = relatorio_completude(df_result, indicador)

        # 7. Salvar modelo
        modelo_path = salvar_modelo(
            clf, reg, encoders["microarea"], encoders["nivel"],
            indicador, list(X.columns), boas_praticas
        )

        # 8. Estatísticas
        stats = {
            "total_pacientes": len(df_result),
            "em_dia": int((df_result["nivel_prioridade"] == "EM DIA").sum()),
            "moderado": int((df_result["nivel_prioridade"] == "MODERADO").sum()),
            "grave": int((df_result["nivel_prioridade"] == "GRAVE").sum()),
            "muito_grave": int((df_result["nivel_prioridade"] == "MUITO GRAVE").sum()),
            "critico": int((df_result["nivel_prioridade"] == "CRÍTICO").sum()),
            "completude_media": round(float(df_result["completude"].mean()), 1),
            "acuracia_modelo": round(float(accuracy), 4),
            "busca_ativa_total": len(df_busca),
            "microareas_relatorio": len(relatorio),
            "modelo_salvo": modelo_path is not None,
        }

        colunas_saida = []
        for col in ["nome", "microarea", "nivel_prioridade", "completude", "qtd_faltante"]:
            if col in df_result.columns:
                colunas_saida.append(col)

        pacientes = df_result[colunas_saida].head(200).to_dict(orient="records")

        return jsonify({
            "indicador": indicador,
            "nome_indicador": INDICADORES[indicador]["nome"],
            "estatisticas": stats,
            "pacientes": pacientes,
            "relatorio_completude": relatorio.to_dict(orient="records"),
            "modelo_path": modelo_path,
        }), 200

    except Exception as e:
        logger.error(f"Erro em /api/pipeline-completo: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@app.route('/api/modelos', methods=['GET'])
def api_listar_modelos():
    """Lista modelos salvos."""
    modelos = []
    modelos_dir = "models"
    if os.path.exists(modelos_dir):
        for f in sorted(os.listdir(modelos_dir)):
            if f.endswith(".pkl"):
                path = os.path.join(modelos_dir, f)
                modelos.append({
                    "arquivo": f,
                    "caminho": path,
                    "tamanho_kb": round(os.path.getsize(path) / 1024, 1),
                    "modificado": datetime.fromtimestamp(
                        os.path.getmtime(path)
                    ).isoformat()
                })
    return jsonify({"modelos": modelos, "total": len(modelos)}), 200

@app.route('/api/modelo/usar', methods=['POST'])
def api_usar_modelo():
    """Carrega um modelo salvo e aplica em um novo CSV."""
    if 'file' not in request.files:
        return jsonify({"error": "Envie um CSV no campo 'file'."}), 400
    if 'modelo' not in request.form:
        return jsonify({"error": "Informe o caminho do modelo no campo 'modelo'."}), 400

    file = request.files['file']
    modelo_path = request.form['modelo']

    if not os.path.exists(modelo_path):
        return jsonify({"error": f"Modelo não encontrado: {modelo_path}"}), 404

    temp_path = "/tmp/temp_modelo.csv"
    file.save(temp_path)

    try:
        resultado = carregar_e_usar_modelo(modelo_path, temp_path)
        return jsonify(resultado), 200
    except Exception as e:
        logger.error(f"Erro em /api/modelo/usar: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

# 
# --- ERROR HANDLERS ---
# 

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Requisição inválida", "detalhe": str(e)}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint não encontrado"}), 404

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "Arquivo muito grande. Limite: 50MB."}), 413

@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Erro interno do servidor"}), 500

# 
# --- ENTRY POINT ---
# 

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    logger.info(f"Iniciando {SYSTEM_TITLE} v{SYSTEM_VERSION} na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
