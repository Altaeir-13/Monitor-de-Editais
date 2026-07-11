FROM python:3.11-slim

# Evita a gravacao de arquivos compilados (.pyc) e desativa o buffering de logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instala dependencias nativas para psycopg2 e comunicacao com Postgres
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Instala dependencias do python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia a aplicacao inteira
COPY . .

# Normaliza line endings do entrypoint para Linux e aplica permissao de execucao
RUN sed -i 's/\r$//' entrypoint.sh && chmod +x entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]
