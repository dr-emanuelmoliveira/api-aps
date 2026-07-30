FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (cache de layers)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código fonte
COPY . .

# Criar diretórios necessários
RUN mkdir -p output static models

# Variável de porta (Railway injeta automaticamente)
ENV PORT=5000
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Expor porta
EXPOSE $PORT

# Iniciar com gunicorn apontando para api.py
CMD gunicorn api:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
