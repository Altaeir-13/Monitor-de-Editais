# Monitor de Editais

Plataforma web para centralizar, visualizar e acompanhar editais de instituições públicas. O sistema inclui autenticação JWT, painel administrativo, catálogo de fontes, crawler institucional, alertas de usuário, notificações internas, scheduler configurável e painel operacional do crawler.

## Status do Projeto

O MVP está funcional para a primeira fase de monitoramento das instituições públicas do Nordeste.

Entregas atuais:

- catálogo Nordeste com seed idempotente;
- crawler em camadas com spiders genérico, WordPress, Gov.br, paginado e SIGAA/JSF;
- deduplicação por fingerprint e URL normalizada;
- endpoint manual `POST /admin/run-crawler`;
- execução por fonte específica no painel operacional;
- scheduler com APScheduler, desativado por padrão;
- painel operacional em `/admin/crawler`;
- auditoria final Nordeste com 1.418 editais recuperados.

Limitações ainda existentes:

- SMTP real ainda precisa ser configurado para entrega efetiva de e-mails;
- deploy em VPS/cloud ainda não foi executado;
- algumas fontes externas podem falhar por SSL, conexão, 404, login ou mudanças no portal de origem.

## Requisitos

- Python 3.11 ou superior compatível com as dependências do projeto.
- Node.js e npm compatíveis com o frontend Vite/React.
- PostgreSQL para homologação/produção.
- SQLite apenas para validação local controlada.
- Docker e Docker Compose, se usar os ambientes conteinerizados.

## Configuração de Ambiente

Nunca versione arquivos `.env` reais com segredos.

Arquivos de exemplo:

- `backend/.env.local.example`: variáveis do backend para desenvolvimento local rápido com SQLite.
- `backend/.env.example`: variáveis do backend para PostgreSQL em homologação ou produção local.
- `frontend/.env.example`: URL da API usada pelo frontend em desenvolvimento.
- `.env.prod.example`: variáveis esperadas no Docker Compose de produção local.

### Backend Local com SQLite

Use este modo para validação local rápida, sem PostgreSQL instalado ou configurado:

```powershell
cd C:\Users\Altair\Documents\Editais\backend
copy .env.local.example .env
venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Se o ambiente virtual ainda não existir, crie antes de ativar:

```powershell
python -m venv venv
```

O backend ficará em `http://127.0.0.1:8000` e a documentação Swagger em `http://127.0.0.1:8000/docs`.

Variáveis principais do modo SQLite:

```env
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=dev-local-change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
CRAWLER_SCHEDULER_ENABLED=false
CRAWLER_INTERVAL_MINUTES=360
```

O arquivo `backend/.env.local.example` também mantém valores locais inofensivos para `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB`, porque as configurações atuais do backend ainda exigem essas variáveis. Elas não são usadas quando `DATABASE_URL` aponta para SQLite.

Não use `backend/audit_northeast_final.db` como banco padrão. Esse arquivo é artefato local de auditoria.

### Backend com PostgreSQL

Use este modo quando quiser validar em um ambiente próximo de homologação:

```powershell
cd C:\Users\Altair\Documents\Editais\backend
copy .env.example .env
venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Ao usar `backend/.env.example`, tenha antes:

- PostgreSQL rodando em `localhost:5432`, ou ajuste `DATABASE_URL`;
- banco `monitor_editais` criado, ou ajuste `POSTGRES_DB` e `DATABASE_URL`;
- usuário e senha compatíveis com `POSTGRES_USER`, `POSTGRES_PASSWORD` e `DATABASE_URL`.

Exemplo de URL PostgreSQL:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/monitor_editais
```

Se preferir subir apenas o banco pelo Docker Compose:

```powershell
cd C:\Users\Altair\Documents\Editais
docker compose up -d db
```

### Frontend

Crie `frontend/.env` a partir do exemplo:

```powershell
copy frontend\.env.example frontend\.env
```

Variável principal:

```env
VITE_API_URL=http://localhost:8000
```

## Rodar em Desenvolvimento

### 1. Backend

```powershell
cd C:\Users\Altair\Documents\Editais\backend
copy .env.local.example .env
venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Por padrão, o comando acima usa SQLite em `backend/app.db`.

### 2. Frontend

```powershell
cd C:\Users\Altair\Documents\Editais\frontend
npm install
npm run dev
```

O frontend ficará em `http://localhost:5173`.

## Criar Usuário Admin

O projeto ainda não possui comando dedicado de criação de admin. Para homologação, use o fluxo existente dos modelos/serviços do backend em ambiente controlado. Exemplo de script Python a executar com o ambiente do backend configurado:

```python
from app.db.session import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.user import create_user

db = SessionLocal()
try:
    email = "admin@example.com"
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = create_user(db, UserCreate(name="Admin", email=email, password="change-me"))
    user.role = "admin"
    user.is_active = True
    db.commit()
finally:
    db.close()
```

Troque e proteja a senha antes de usar em homologação/produção.

## Seed Nordeste

Com o backend rodando e usuário admin autenticado, execute:

```http
POST /admin/seed-northeast
```

O seed é idempotente: pode ser executado novamente sem duplicar instituições ou fontes. Fontes substituídas via `replaces` são atualizadas/desativadas conforme a regra do catálogo.

## Crawler

Execução manual geral:

```http
POST /admin/run-crawler
```

Execução manual por fonte específica:

```http
POST /admin/run-crawler/source/{source_id}
```

Painel operacional:

```text
/admin/crawler
```

No painel, o administrador acompanha:

- saúde geral do crawler;
- fontes OK, com erro, sem itens, nunca checadas e inativas;
- última checagem;
- último sucesso;
- último erro;
- itens encontrados e novos salvos;
- histórico recente de execuções;
- execução geral ou por fonte.

## Scheduler do Crawler

O backend possui suporte à execução agendada usando APScheduler.

Por padrão, mantenha desativado:

```env
CRAWLER_SCHEDULER_ENABLED=false
CRAWLER_INTERVAL_MINUTES=360
```

Para ativar em ambiente controlado:

```env
CRAWLER_SCHEDULER_ENABLED=true
CRAWLER_INTERVAL_MINUTES=360
```

Com essa configuração, o backend executa o crawler automaticamente a cada 360 minutos.

Observações:

- o scheduler usa sessão própria do banco;
- o job usa `max_instances=1` e `coalesce=True`;
- falhas são registradas em log e não derrubam a aplicação;
- em desenvolvimento, mantenha `CRAWLER_SCHEDULER_ENABLED=false`.

## Rodar Local-Prod com Docker Compose

Configure as variáveis obrigatórias e suba o ambiente:

```powershell
$env:SECRET_KEY="SUA_CHAVE_FORTE"
$env:POSTGRES_PASSWORD="SENHA_FORTE_DO_BANCO"
docker compose -f docker-compose.prod.yml up -d --build
```

Acesse:

```text
http://localhost
```

Se o volume do Postgres já existir, alterar `POSTGRES_PASSWORD` não altera a senha interna do banco. Para testes limpos, remova volumes somente quando não houver dados relevantes.

## Testes e Validações

Backend:

```powershell
cd backend
venv\Scripts\python.exe tests\test_crawler.py
```

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

Auditoria Nordeste em banco controlado:

```powershell
cd backend
venv\Scripts\python.exe scripts\audit_northeast_sources.py --database-url sqlite:///C:/caminho/para/audit_northeast_final.db
```

Não versione bancos de auditoria.

## Documentação Operacional

- `docs/operacao.md`: guia de operação do crawler e interpretação do painel.
- `docs/checklist_homologacao.md`: checklist para homologação.
- `docs/auditoria_fontes_nordeste.md`: relatório da auditoria final das fontes Nordeste.

## Não Versionar

- `.env` reais;
- `venv/`;
- `node_modules/`;
- `dist/`;
- `__pycache__/`;
- bancos SQLite locais (`*.db`, `*.sqlite`, `*.sqlite3`);
- bancos de auditoria temporários.

## Licença

Este projeto é disponibilizado sob a Licença de Uso Não Comercial — Monitor de Editais.

Consulte `LICENSE.md` para os termos completos.