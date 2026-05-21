#!/bin/sh
set -e

# Executa as migrações automáticas do banco de dados na inicialização
echo "Aguardando inicialização do banco de dados e aplicando migrações..."
alembic upgrade head

# Inicia o Uvicorn apontando para a aplicação FastAPI em modo produção
echo "Iniciando o servidor FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
