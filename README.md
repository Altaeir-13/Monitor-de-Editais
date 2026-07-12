# Monitor de Editais

Plataforma web para centralizar, visualizar e acompanhar editais de instituiÃƒÂ§ÃƒÂµes pÃƒÂºblicas. O sistema inclui autenticaÃƒÂ§ÃƒÂ£o JWT, painel administrativo, catÃƒÂ¡logo de fontes, crawler institucional, alertas de usuÃƒÂ¡rio, notificaÃƒÂ§ÃƒÂµes internas, scheduler configurÃƒÂ¡vel e painel operacional do crawler.

## Status do Projeto

O MVP estÃƒÂ¡ funcional para a primeira fase de monitoramento das instituiÃƒÂ§ÃƒÂµes pÃƒÂºblicas do Nordeste.

Entregas atuais:

- catÃƒÂ¡logo Nordeste com seed idempotente;
- crawler em camadas com spiders genÃƒÂ©rico, WordPress, Gov.br, paginado e SIGAA/JSF;
- deduplicaÃƒÂ§ÃƒÂ£o por fingerprint e URL normalizada;
- endpoint manual `POST /admin/run-crawler`;
- execuÃƒÂ§ÃƒÂ£o por fonte especÃƒÂ­fica no painel operacional;
- scheduler com APScheduler, desativado por padrÃƒÂ£o;
- painel operacional em `/admin/crawler`;
- auditoria final Nordeste com 1.418 editais recuperados.

LimitaÃƒÂ§ÃƒÂµes ainda existentes:

- SMTP real ainda precisa ser configurado para entrega efetiva de e-mails;
- deploy em VPS/cloud ainda nÃƒÂ£o foi executado;
- algumas fontes externas podem falhar por SSL, conexÃƒÂ£o, 404, login ou mudanÃƒÂ§as no portal de origem.

## Requisitos

- Python 3.11 ou superior compatÃƒÂ­vel com as dependÃƒÂªncias do projeto.
- Node.js e npm compatÃƒÂ­veis com o frontend Vite/React.
- PostgreSQL para homologaÃƒÂ§ÃƒÂ£o/produÃƒÂ§ÃƒÂ£o.
- SQLite apenas para validaÃƒÂ§ÃƒÂ£o local controlada.
- Docker e Docker Compose, se usar os ambientes conteinerizados.

## ConfiguraÃƒÂ§ÃƒÂ£o de Ambiente

Nunca versione arquivos `.env` reais com segredos.

Arquivos de exemplo:

- `backend/.env.local.example`: variÃƒÂ¡veis do backend para desenvolvimento local rÃƒÂ¡pido com SQLite.
- `backend/.env.example`: variÃƒÂ¡veis do backend para PostgreSQL em homologaÃƒÂ§ÃƒÂ£o ou produÃƒÂ§ÃƒÂ£o local.
- `frontend/.env.example`: URL da API usada pelo frontend em desenvolvimento.
- `.env.prod.example`: variÃƒÂ¡veis esperadas no Docker Compose de produÃƒÂ§ÃƒÂ£o local.

### Backend Local com SQLite

Use este modo para validaÃƒÂ§ÃƒÂ£o local rÃƒÂ¡pida, sem PostgreSQL instalado ou configurado:

```powershell
cd C:\Users\Altair\Documents\Working\Development\Monitor\ de\ Editais\backend
copy .env.local.example .env
venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Se o ambiente virtual ainda nÃƒÂ£o existir, crie antes de ativar:

```powershell
python -m venv venv
```

O backend ficarÃƒÂ¡ em `http://127.0.0.1:8000` e a documentaÃƒÂ§ÃƒÂ£o Swagger em `http://127.0.0.1:8000/docs`.

VariÃƒÂ¡veis principais do modo SQLite:

```env
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=dev-local-change-me
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
CRAWLER_SCHEDULER_ENABLED=false
CRAWLER_INTERVAL_MINUTES=360
```

O arquivo `backend/.env.local.example` tambÃƒÂ©m mantÃƒÂ©m valores locais inofensivos para `POSTGRES_USER`, `POSTGRES_PASSWORD` e `POSTGRES_DB`, porque as configuraÃƒÂ§ÃƒÂµes atuais do backend ainda exigem essas variÃƒÂ¡veis. Elas nÃƒÂ£o sÃƒÂ£o usadas quando `DATABASE_URL` aponta para SQLite.

NÃƒÂ£o use `backend/audit_northeast_final.db` como banco padrÃƒÂ£o. Esse arquivo ÃƒÂ© artefato local de auditoria.

### Backend com PostgreSQL

Use este modo quando quiser validar em um ambiente prÃƒÂ³ximo de homologaÃƒÂ§ÃƒÂ£o:

```powershell
cd C:\Users\Altair\Documents\Working\Development\Monitor\ de\ Editais\backend
copy .env.example .env
venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Ao usar `backend/.env.example`, tenha antes:

- PostgreSQL rodando em `localhost:5432`, ou ajuste `DATABASE_URL`;
- banco `monitor_editais` criado, ou ajuste `POSTGRES_DB` e `DATABASE_URL`;
- usuÃƒÂ¡rio e senha compatÃƒÂ­veis com `POSTGRES_USER`, `POSTGRES_PASSWORD` e `DATABASE_URL`.

Exemplo de URL PostgreSQL:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/monitor_editais
```

Se preferir subir apenas o banco pelo Docker Compose:

```powershell
cd C:\Users\Altair\Documents\Working\Development\Monitor\ de\ Editais
docker compose up -d db
```

### Frontend

Crie `frontend/.env` a partir do exemplo:

```powershell
copy frontend\.env.example frontend\.env
```

VariÃƒÂ¡vel principal:

```env
VITE_API_URL=http://localhost:8000
```

## Rodar em Desenvolvimento

### 1. Backend

```powershell
cd C:\Users\Altair\Documents\Working\Development\Monitor\ de\ Editais\backend
copy .env.local.example .env
venv\Scripts\activate
pip install -r requirements.txt
python -m alembic upgrade head
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Por padrÃƒÂ£o, o comando acima usa SQLite em `backend/app.db`.

### 2. Frontend

```powershell
cd C:\Users\Altair\Documents\Working\Development\Monitor\ de\ Editais\frontend
npm install
npm run dev
```

O frontend ficarÃƒÂ¡ em `http://localhost:5173`.

## Criar usuario admin

Use o script idempotente do backend:

```powershell
python scripts/create_admin.py --name "Administrador" --email "admin@example.com"
```

Forneca ADMIN_PASSWORD apenas pelo ambiente do processo. O script cria, promove ou reativa o usuario e nunca imprime a senha.

## Seed Nordeste

Com o backend rodando e usuÃƒÂ¡rio admin autenticado, execute:

```http
POST /admin/seed-northeast
```

O seed ÃƒÂ© idempotente: pode ser executado novamente sem duplicar instituiÃƒÂ§ÃƒÂµes ou fontes. Fontes substituÃƒÂ­das via `replaces` sÃƒÂ£o atualizadas/desativadas conforme a regra do catÃƒÂ¡logo.

## Crawler

ExecuÃƒÂ§ÃƒÂ£o manual geral:

```http
POST /admin/run-crawler
```

ExecuÃƒÂ§ÃƒÂ£o manual por fonte especÃƒÂ­fica:

```http
POST /admin/run-crawler/source/{source_id}
```

Painel operacional:

```text
/admin/crawler
```

No painel, o administrador acompanha:

- saÃƒÂºde geral do crawler;
- fontes OK, com erro, sem itens, nunca checadas e inativas;
- ÃƒÂºltima checagem;
- ÃƒÂºltimo sucesso;
- ÃƒÂºltimo erro;
- itens encontrados e novos salvos;
- histÃƒÂ³rico recente de execuÃƒÂ§ÃƒÂµes;
- execuÃƒÂ§ÃƒÂ£o geral ou por fonte.

## Scheduler do Crawler

O backend possui suporte ÃƒÂ  execuÃƒÂ§ÃƒÂ£o agendada usando APScheduler.

Por padrÃƒÂ£o, mantenha desativado:

```env
CRAWLER_SCHEDULER_ENABLED=false
CRAWLER_INTERVAL_MINUTES=360
```

Para ativar em ambiente controlado:

```env
CRAWLER_SCHEDULER_ENABLED=true
CRAWLER_INTERVAL_MINUTES=360
```

Com essa configuraÃƒÂ§ÃƒÂ£o, o backend executa o crawler automaticamente a cada 360 minutos.

ObservaÃƒÂ§ÃƒÂµes:

- o scheduler usa sessÃƒÂ£o prÃƒÂ³pria do banco;
- o job usa `max_instances=1` e `coalesce=True`;
- falhas sÃƒÂ£o registradas em log e nÃƒÂ£o derrubam a aplicaÃƒÂ§ÃƒÂ£o;
- em desenvolvimento, mantenha `CRAWLER_SCHEDULER_ENABLED=false`.

## Rodar Local-Prod com Docker Compose

Configure as variÃƒÂ¡veis obrigatÃƒÂ³rias e suba o ambiente:

```powershell
$env:SECRET_KEY="SUA_CHAVE_FORTE"
$env:POSTGRES_PASSWORD="SENHA_FORTE_DO_BANCO"
docker compose -f docker-compose.prod.yml up -d --build
```

Acesse:

```text
http://localhost
```

Se o volume do Postgres jÃƒÂ¡ existir, alterar `POSTGRES_PASSWORD` nÃƒÂ£o altera a senha interna do banco. Para testes limpos, remova volumes somente quando nÃƒÂ£o houver dados relevantes.

## Testes e ValidaÃƒÂ§ÃƒÂµes

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

NÃƒÂ£o versione bancos de auditoria.

## DocumentaÃƒÂ§ÃƒÂ£o Operacional

- `docs/operacao.md`: guia de operaÃƒÂ§ÃƒÂ£o do crawler e interpretaÃƒÂ§ÃƒÂ£o do painel.
- `docs/checklist_homologacao.md`: checklist para homologaÃƒÂ§ÃƒÂ£o.
- `docs/auditoria_fontes_nordeste.md`: relatÃƒÂ³rio da auditoria final das fontes Nordeste.

## NÃƒÂ£o Versionar

- `.env` reais;
- `venv/`;
- `node_modules/`;
- `dist/`;
- `__pycache__/`;
- bancos SQLite locais (`*.db`, `*.sqlite`, `*.sqlite3`);
- bancos de auditoria temporÃƒÂ¡rios.

## LicenÃƒÂ§a

Este projeto ÃƒÂ© disponibilizado sob a LicenÃƒÂ§a de Uso NÃƒÂ£o Comercial Ã¢â‚¬â€ Monitor de Editais.

Consulte `LICENSE.md` para os termos completos.

## Homologacao com Docker e PostgreSQL

Este fluxo valida um ambiente reproduzivel com PostgreSQL, migrations Alembic, backend FastAPI, frontend buildado, seed Nordeste, admin, crawler manual e scheduler desligado por padrao.

### 1. Preparar variaveis

```powershell
cd "C:\Users\Altair\Documents\Working\Development\Monitor de Editais"
copy .env.prod.example .env
notepad .env
```

Antes de subir o ambiente, substitua no `.env`:

- `POSTGRES_PASSWORD` por uma senha real;
- `SECRET_KEY` por um valor longo e aleatorio;
- `BACKEND_CORS_ORIGINS` pelos dominios reais de homologacao;
- `ADMIN_EMAIL` pelo e-mail do administrador;
- `ADMIN_PASSWORD` somente se preferir automacao local. Para uso interativo, deixe vazio e digite a senha no prompt.

Mantenha inicialmente:

```env
CRAWLER_SCHEDULER_ENABLED=false
CRAWLER_INTERVAL_MINUTES=360
```

### 2. Validar Compose e subir

```powershell
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d db
docker compose -f docker-compose.prod.yml up -d backend frontend
docker compose -f docker-compose.prod.yml ps
docker compose -f docker-compose.prod.yml logs backend --tail=100
```

O backend executa `alembic upgrade head` no `entrypoint.sh`. O PostgreSQL possui health check com `pg_isready`; o backend aguarda o banco saudavel e expoe `/ready`; o frontend aguarda o backend saudavel e serve o build de producao via Nginx.

### 3. Criar administrador

Com senha interativa:

```powershell
docker compose -f docker-compose.prod.yml exec backend python scripts/create_admin.py --name "Administrador" --email "admin@example.com"
```

Ou com senha por variavel de ambiente local, sem exibir a senha no comando:

```powershell
$env:ADMIN_PASSWORD = Read-Host "Senha admin"
docker compose -f docker-compose.prod.yml exec -e ADMIN_PASSWORD=$env:ADMIN_PASSWORD backend python scripts/create_admin.py --name "Administrador" --email "admin@example.com"
Remove-Item Env:\ADMIN_PASSWORD
```

O script e idempotente: cria o admin, nao duplica se ja existir e promove usuario existente para `admin` quando necessario.

### 4. Validar saude e API

```powershell
Invoke-RestMethod http://localhost/api/health
Invoke-RestMethod http://localhost/api/ready
Invoke-RestMethod http://localhost/api/openapi.json
```

### 5. Executar smoke test

```powershell
$env:SMOKE_BASE_URL = "http://localhost/api"
$env:SMOKE_ADMIN_EMAIL = "admin@example.com"
$env:SMOKE_ADMIN_PASSWORD = Read-Host "Senha admin"
docker compose -f docker-compose.prod.yml exec -e SMOKE_BASE_URL=$env:SMOKE_BASE_URL -e SMOKE_ADMIN_EMAIL=$env:SMOKE_ADMIN_EMAIL -e SMOKE_ADMIN_PASSWORD=$env:SMOKE_ADMIN_PASSWORD backend python scripts/smoke_test.py
Remove-Item Env:\SMOKE_BASE_URL
Remove-Item Env:\SMOKE_ADMIN_EMAIL
Remove-Item Env:\SMOKE_ADMIN_PASSWORD
```

O smoke test verifica `/health`, `/ready`, OpenAPI, login admin, listagem de fontes, status do crawler e listagem publica de editais. Ele nao executa crawler geral.

### 6. Seed Nordeste e crawler manual

Use o token do login admin ou a interface administrativa.

```powershell
$login = Invoke-RestMethod -Method Post -Uri http://localhost/api/auth/login -ContentType "application/x-www-form-urlencoded" -Body @{ username = "admin@example.com"; password = "SENHA_ADMIN" }
$headers = @{ Authorization = "Bearer $($login.access_token)" }

Invoke-RestMethod -Method Post -Uri http://localhost/api/admin/seed-northeast -Headers $headers
Invoke-RestMethod -Method Post -Uri http://localhost/api/admin/seed-northeast -Headers $headers
Invoke-RestMethod -Uri http://localhost/api/admin/sources -Headers $headers
Invoke-RestMethod -Uri http://localhost/api/admin/crawler/status -Headers $headers
Invoke-RestMethod -Uri http://localhost/api/admin/crawler/sources-status -Headers $headers
```

Para validar uma fonte especifica, escolha um `source_id` ativo e execute:

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost/api/admin/run-crawler/source/ID_DA_FONTE -Headers $headers
Invoke-RestMethod -Uri http://localhost/api/admin/crawler/runs -Headers $headers
Invoke-RestMethod -Uri http://localhost/api/notices/
```

Registre os numeros retornados nesta homologacao: instituicoes, fontes, fontes ativas, fontes verificadas, itens encontrados, novos itens, fontes com falha e editais salvos. Nao reutilize numeros historicos da auditoria Nordeste como resultado novo.

### 7. Testar scheduler somente depois

Depois de validar seed, painel e crawler manual, edite `.env`:

```env
CRAWLER_SCHEDULER_ENABLED=true
CRAWLER_INTERVAL_MINUTES=360
```

Recrie apenas o backend:

```powershell
docker compose -f docker-compose.prod.yml up -d --build backend
docker compose -f docker-compose.prod.yml logs backend --tail=200
```

Confirme nos logs inicio e fim do scheduler. Mantenha uma unica instancia do backend quando o scheduler estiver habilitado.

### 8. Backup e rollback basicos

Backup:

```powershell
docker compose -f docker-compose.prod.yml exec db pg_dump -U postgres -d monitor_editais > backup_monitor_editais.sql
```

Rollback operacional simples:

```powershell
docker compose -f docker-compose.prod.yml logs backend --tail=200
docker compose -f docker-compose.prod.yml restart backend
```

Rollback destrutivo de banco deve ser feito apenas com aprovacao explicita e backup conferido.

### Validacao controlada do scheduler

O scheduler deve permanecer desativado por padrao. Quando for necessario validar agendamento, use um ambiente descartavel, uma unica instancia do backend e intervalo curto temporario:

```env
CRAWLER_SCHEDULER_ENABLED=true
CRAWLER_INTERVAL_MINUTES=1
```

Verifique os logs do backend para confirmar registro do job, inicio, conclusao, falha e encerramento. Nao habilite o scheduler em multiplos workers ou replicas sem coordenacao externa, pois cada processo pode iniciar um APScheduler proprio.

## Homologacao remota com HTTPS

O fluxo remoto canonico esta em
[`docs/deploy_homologacao_remota.md`](docs/deploy_homologacao_remota.md).
Ele define Nginx como proxy unico, frontend buildado, API em `/api`,
PostgreSQL interno, migration one-shot, certificados externos, scripts de
deploy/smoke/backup/restore e rollback controlado.

Validacao local declarativa:

```powershell
docker compose --env-file .env.prod.example -f docker-compose.prod.yml config --quiet
docker compose --env-file .env.prod.example -f docker-compose.prod.yml build
```

Para implantacao futura, copie o exemplo para `.env.prod`, substitua todos os
placeholders, forneca os certificados fora do Git e use:

```powershell
pwsh -File scripts/deploy.ps1 -EnvFile .env.prod -ProjectName monitor-editais-staging
```

Deploy real, DNS, certificado, commit e push permanecem acoes manuais.
