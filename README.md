# Monitor de Editais

Aplicação web para reunir editais publicados por instituições públicas em fontes oficiais, reduzir a dispersão das consultas e apoiar o acompanhamento operacional da coleta. O projeto atende pessoas interessadas em oportunidades públicas e equipes responsáveis pelo cadastro de instituições, fontes e rotinas de monitoramento.

O sistema está em estágio de MVP funcional. A topologia de homologação com PostgreSQL, FastAPI, React, Nginx e HTTPS foi preparada e validada localmente; a implantação em um servidor remoto ainda depende de DNS, certificado, segredos e operação do ambiente. Isso não representa uma produção concluída.

O inventário institucional possui alcance nacional. A cobertura operacional das fontes permanece em validação progressiva.

## Principais funcionalidades

- catálogo nacional auditável de instituições públicas e fontes oficiais, com seed idempotente nacional e wrapper compatível para o Nordeste;
- crawlers genérico, WordPress, Gov.br, paginado e SIGAA/JSF;
- normalização de títulos e URLs, fingerprint SHA-256 e deduplicação;
- classificação normalizada por tipo de edital e filtros de consulta;
- endpoints públicos da API para listar e detalhar editais;
- autenticação JWT, cadastro de usuários e controle de acesso administrativo;
- alertas por palavra-chave e tipo de edital, notificações internas e suporte a SMTP;
- administração de instituições e fontes monitoradas;
- painel operacional do crawler em `/admin/crawler`;
- execução manual geral ou por fonte;
- scheduler com APScheduler, configurável e desativado por padrão.

A API `GET /notices/` e o detalhe `GET /notices/{notice_id}` não exigem autenticação. Na SPA atual, porém, as páginas `/notices` e `/notices/:id` ficam em uma rota protegida e exigem login; somente `/login` e `/register` são páginas públicas.

## Escopo nacional auditável

A fonte canônica são os Microdados do Censo da Educação Superior 2024 do Inep,
com os filtros `NU_ANO_CENSO = 2024` e `TP_REDE = 1`. A reconciliação preserva
as instituições excluídas no inventário para que decisões de escopo continuem
auditáveis.

| Métrica | Total |
|---|---:|
| Registros públicos no Censo | 317 |
| Registros censitários elegíveis | 315 |
| Instituições posteriores ao Censo | 3 |
| Inventário auditável, incluindo excluídas | 320 |
| Alvo operacional elegível | 318 |
| Fontes no inventário completo | 303 |
| Fontes associadas a instituições elegíveis | 302 |
| Instituições elegíveis com fonte | 263 |
| Instituições elegíveis sem fonte | 55 |
| Instituições com status `verified` | 93 |
| Instituições com status `partial` | 165 |
| Instituições em `manual_review` | 29 |
| Instituições em `source_not_found` | 31 |
| Instituições com captura validada | 0 |
| Instituições em monitoramento ativo | 0 |

Inventário, fonte mapeada, fonte verificada, captura validada e monitoramento
ativo são estágios diferentes. Uma URL `verified` indica verificação da fonte,
não uma captura validada. Captura validada, por sua vez, não habilita
monitoramento contínuo. As fontes introduzidas pelo catálogo nacional começam
inativas e o scheduler remoto permanece com `CRAWLER_SCHEDULER_ENABLED=false`.
Metodologia, totais regionais, checksums e limitações estão em [Cobertura
nacional](docs/cobertura_nacional.md).

## Arquitetura

```text
Internet
  |
HTTPS / Nginx
  +-- React SPA
  +-- /api -> FastAPI
                  |
               PostgreSQL
```

Na topologia de homologação:

- Nginx é o único serviço público e publica as portas 80 e 443;
- HTTP é redirecionado para HTTPS;
- a SPA e a API usam a mesma origem, com `VITE_API_URL=/api` e `API_ROOT_PATH=/api`;
- FastAPI não publica porta no host e participa das redes `edge` e `data`;
- PostgreSQL não publica porta e fica na rede interna `data`;
- o volume do PostgreSQL é persistente e escopado pelo project name do Compose;
- o serviço one-shot `migrate` executa `alembic upgrade head` antes do backend;
- `/health` verifica o processo e `/ready` também verifica a conexão com o banco;
- OpenAPI é configurável e começa desabilitado na configuração remota de exemplo;
- o scheduler começa desativado.

SQLite é destinado ao desenvolvimento e aos testes locais isolados. Homologação compartilhada e produção usam PostgreSQL.

## Tecnologias

### Backend

- Python e FastAPI;
- Uvicorn;
- SQLAlchemy e Alembic;
- Pydantic Settings;
- autenticação JWT;
- APScheduler;
- Requests e Beautiful Soup para coleta e parsing.

### Frontend

- React 19;
- React Router 7;
- TypeScript 6;
- Vite 8;
- Axios;
- TanStack Query;
- Tailwind CSS 4.

### Banco e infraestrutura

- SQLite para desenvolvimento e testes locais;
- PostgreSQL 15 na imagem do Compose;
- Docker e Docker Compose;
- Nginx para SPA, TLS e proxy reverso;
- scripts PowerShell para deploy, smoke, backup e restauração.

### Validação

- scripts de teste Python com bancos SQLite temporários;
- ESLint, TypeScript e build Vite;
- healthchecks do Compose;
- smoke test autenticado sem execução do crawler geral.

## Estrutura do projeto

```text
.
|-- backend/
|   |-- app/                 # API, modelos, serviços, crawler e configuração
|   |-- alembic/             # migrations
|   |-- scripts/             # admin, smoke e auditoria controlada
|   +-- tests/               # suíte backend
|-- frontend/
|   |-- public/
|   |-- src/                 # páginas, componentes, hooks e serviços
|   |-- Dockerfile
|   +-- nginx.conf
|-- deploy/certs/            # ponto local ignorado para certificados de validação
|-- docs/                    # guias operacionais e de homologação
|-- scripts/                 # deploy, smoke, backup e restauração PostgreSQL
|-- docker-compose.yml       # apoio ao desenvolvimento
|-- docker-compose.prod.yml  # topologia de homologação/produção
|-- .env.prod.example
+-- AGENTS.md
```

## Requisitos

- Python 3.11 para reproduzir o runtime do container. A suíte também foi validada localmente com Python 3.14.5.
- Node.js 22.12 ou superior da linha 22. O Vite atual aceita `^20.19.0` ou `>=22.12.0`, e o Dockerfile usa Node 22.
- npm compatível com a versão do Node.js e com o `package-lock.json`. A validação local usou npm 11.13.0.
- Docker Engine com o plugin Docker Compose v2 para os ambientes conteinerizados.
- Windows PowerShell 5.1 para os scripts locais validados. Em servidores Linux, instale PowerShell 7 e use `pwsh`.
- PostgreSQL somente quando o backend for executado fora do Compose com a configuração PostgreSQL.

## Execução local

Execute os comandos desta seção a partir da raiz do repositório, salvo indicação em contrário.

### Backend com SQLite

```powershell
Set-Location .\backend

if (-not (Test-Path .\.env)) {
    Copy-Item .\.env.local.example .\.env
}

if (-not (Test-Path .\venv)) {
    python -m venv venv
}

.\venv\Scripts\python.exe -m pip install -r .\requirements.txt
.\venv\Scripts\python.exe -m alembic upgrade head
.\venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

O exemplo local usa `DATABASE_URL=sqlite:///./app.db`. O arquivo `backend/.env` e o banco local são ignorados pelo Git. Não use bancos de auditoria como banco padrão.

Com o backend em execução:

- API: `http://127.0.0.1:8000`;
- health: `http://127.0.0.1:8000/health`;
- readiness: `http://127.0.0.1:8000/ready`;
- Swagger local: `http://127.0.0.1:8000/docs`.

### Criar ou atualizar o administrador

A partir de `backend`:

```powershell
.\venv\Scripts\python.exe .\scripts\create_admin.py --name "Administrador" --email "admin@example.com"
```

O script solicita a senha sem exibi-la, é idempotente e pode criar, promover ou reativar o usuário. Não grave a senha no comando nem no Git.

### Aplicar o seed nacional

Com um administrador criado e o backend local em execução:

```powershell
$AdminSecret = Read-Host "Senha do administrador" -AsSecureString
$AdminPassword = [Net.NetworkCredential]::new("", $AdminSecret).Password
try {
    $Login = Invoke-RestMethod `
        -Method Post `
        -Uri "http://127.0.0.1:8000/auth/login" `
        -ContentType "application/x-www-form-urlencoded" `
        -Body @{ username = "admin@example.com"; password = $AdminPassword }

    $Headers = @{ Authorization = "Bearer $($Login.access_token)" }

    Invoke-RestMethod `
        -Method Post `
        -Uri "http://127.0.0.1:8000/admin/seed-national" `
        -Headers $Headers
}
finally {
    Remove-Variable AdminPassword, AdminSecret, Login, Headers -ErrorAction SilentlyContinue
}
```

O seed nacional pode ser executado para todo o alvo elegível ou filtrado por
região e repetido sem duplicar instituições ou fontes. Ele ignora registros
excluídos e cria fontes novas com `is_active=false`. O endpoint legado
`POST /admin/seed-northeast` permanece como wrapper compatível do mesmo serviço,
limitado ao Nordeste. Na topologia Nginx, acrescente o prefixo público `/api`
às rotas da API.

### Frontend local

Em outro terminal, a partir da raiz:

```powershell
Set-Location .\frontend

if (-not (Test-Path .\.env)) {
    Copy-Item .\.env.example .\.env
}

npm ci
npm run dev
```

`frontend/.env.example` define `VITE_API_URL=http://localhost:8000`. O Vite disponibiliza a aplicação em `http://localhost:5173` por padrão.

## Execução com Docker, PostgreSQL e HTTPS

A topologia de `docker-compose.prod.yml` exige TLS inclusive na validação local.

### 1. Preparar configuração e certificado

A partir da raiz:

```powershell
if (-not (Test-Path .\.env.prod)) {
    Copy-Item .\.env.prod.example .\.env.prod
}
```

Edite `.env.prod` e substitua todos os placeholders. No mínimo:

- use `ENVIRONMENT=staging`;
- defina `POSTGRES_PASSWORD` e `SECRET_KEY` com valores não-placeholder;
- mantenha `API_ROOT_PATH=/api` e `VITE_API_URL=/api`;
- use origens HTTPS explícitas em `BACKEND_CORS_ORIGINS`;
- mantenha `UVICORN_WORKERS=1`;
- mantenha `CRAWLER_SCHEDULER_ENABLED=false`;
- ajuste `STAGING_DOMAIN`, `HTTP_PORT` e `HTTPS_PORT`;
- aponte `TLS_CERT_DIRECTORY` para um diretório com `fullchain.pem` e `privkey.pem`.

Certificados e chaves nunca devem entrar no Git. Para uma validação local descartável, consulte [o ponto de montagem TLS](deploy/certs/README.md). Em homologação pública, use um certificado válido emitido para o domínio.

### 2. Validar, construir e subir

```powershell
docker compose --env-file .env.prod -f docker-compose.prod.yml config --quiet
docker compose --env-file .env.prod -f docker-compose.prod.yml build
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --wait
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose --env-file .env.prod -f docker-compose.prod.yml logs --tail=100 migrate backend frontend
```

O serviço `migrate` termina com código zero antes de o backend iniciar. O frontend só inicia depois que o backend está saudável.

Com as portas padrão e um certificado local autoassinado:

```powershell
curl.exe -I http://localhost/health
curl.exe -k https://localhost/health
curl.exe -k https://localhost/ready
curl.exe -k https://localhost/api/
```

Use `-k` somente em validação local com certificado autoassinado. Não desabilite a verificação TLS na homologação pública.

`OPENAPI_ENABLED=false` é o padrão remoto; nesse caso, `/api/openapi.json`, `/api/docs` e `/api/redoc` retornam 404. Habilite OpenAPI apenas quando houver uma decisão operacional explícita.

### 3. Encerrar sem apagar dados

```powershell
docker compose --env-file .env.prod -f docker-compose.prod.yml down
```

Esse comando remove containers e redes do projeto, mas preserva o volume nomeado. Não use `down -v` como encerramento padrão. A remoção de volumes exige project name conhecido, backup conferido e autorização explícita.

## Homologação remota

O procedimento canônico está em [Deploy de homologação remota](docs/deploy_homologacao_remota.md). O fluxo, sem duplicar o guia, é:

1. apontar o DNS do domínio para o servidor;
2. liberar somente as portas 80 e 443;
3. instalar Docker e disponibilizar `pwsh`;
4. colocar `fullchain.pem` e `privkey.pem` fora do Git;
5. criar `.env.prod` com domínio, TLS, banco, autenticação, CORS e smoke;
6. validar e executar `scripts/deploy.ps1`;
7. confirmar a migration one-shot, health e readiness;
8. criar o administrador;
9. aplicar o seed nacional, mantendo as fontes novas inativas;
10. executar o smoke remoto;
11. criar e testar backup;
12. manter o scheduler desativado na validação inicial.

Com as entradas operacionais prontas:

```powershell
pwsh -NoProfile -File .\scripts\deploy.ps1 `
    -EnvFile .\.env.prod `
    -ProjectName monitor-editais-staging
```

DNS, certificado real, segredos, acesso ao servidor e decisão de ativar o scheduler são ações manuais. O preparo do repositório não significa que a implantação remota já ocorreu.

## Variáveis de ambiente

Os exemplos versionados são `backend/.env.local.example`, `backend/.env.example`, `frontend/.env.example` e `.env.prod.example`.

| Categoria | Variáveis principais | Observações |
|---|---|---|
| Aplicação | `ENVIRONMENT`, `LOG_LEVEL` | `staging` e `production` ativam validações mais rígidas. |
| Banco | `DATABASE_URL`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` | O Compose monta `DATABASE_URL` para o backend. |
| Autenticação | `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | A chave remota deve ter pelo menos 32 caracteres e não pode ser placeholder. |
| CORS | `BACKEND_CORS_ORIGINS` | Em ambiente remoto, use somente origens HTTPS explícitas. |
| API e proxy | `API_ROOT_PATH`, `OPENAPI_ENABLED`, `UVICORN_WORKERS`, `FORWARDED_ALLOW_IPS` | A topologia documentada usa `API_ROOT_PATH=/api`. |
| Frontend | `VITE_API_URL` | Use `/api` no build de mesma origem. |
| Compose | `COMPOSE_PROJECT_NAME`, `IMAGE_TAG`, `STAGING_DOMAIN`, `HTTP_PORT`, `HTTPS_PORT` | O project name também escopa o volume. |
| TLS | `TLS_CERT_DIRECTORY` | Deve conter `fullchain.pem` e `privkey.pem` fora do Git. |
| Administrador | `ADMIN_NAME`, `ADMIN_EMAIL`, `ADMIN_PASSWORD` | Forneça a senha apenas pelo processo ou prompt. |
| SMTP | `SMTP_TLS`, `SMTP_PORT`, `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAILS_FROM_EMAIL` | Entrega real depende de um provedor configurado. |
| Scheduler | `CRAWLER_SCHEDULER_ENABLED`, `CRAWLER_INTERVAL_MINUTES` | Começa desativado. |
| Smoke | `SMOKE_BASE_URL`, `SMOKE_API_PREFIX`, `SMOKE_ADMIN_EMAIL`, `SMOKE_ADMIN_PASSWORD`, `SMOKE_EXPECT_OPENAPI`, `SMOKE_TLS_VERIFY`, `SMOKE_TIMEOUT` | `SMOKE_BASE_URL` recebe somente a origem, sem `/api`. |

Nunca coloque valores reais de `SECRET_KEY`, `POSTGRES_PASSWORD`, `ADMIN_PASSWORD`, `SMOKE_ADMIN_PASSWORD` ou `SMTP_PASSWORD` em arquivos versionados ou no histórico do shell.

## Testes

### Backend

Execute a partir de `backend`. Cada teste que grava dados seleciona um SQLite temporário isolado antes de importar as configurações.

```powershell
.\venv\Scripts\python.exe -m compileall app tests scripts
.\venv\Scripts\python.exe tests\test_scheduler.py
.\venv\Scripts\python.exe tests\test_sqlite_compatibility.py
.\venv\Scripts\python.exe tests\test_auth.py
.\venv\Scripts\python.exe tests\test_crawler.py
.\venv\Scripts\python.exe tests\test_create_admin.py
.\venv\Scripts\python.exe tests\test_health.py
.\venv\Scripts\python.exe tests\test_config.py
.\venv\Scripts\python.exe tests\test_smoke_test.py
.\venv\Scripts\python.exe tests\test_seed.py
.\venv\Scripts\python.exe tests\test_national_catalog.py
.\venv\Scripts\python.exe tests\test_source_manifests.py
.\venv\Scripts\python.exe tests\test_catalog_eligibility.py
.\venv\Scripts\python.exe tests\test_national_seed.py
.\venv\Scripts\python.exe tests\test_coverage.py
.\venv\Scripts\python.exe tests\test_source_audit.py
.\venv\Scripts\python.exe tests\test_notices.py
.\venv\Scripts\python.exe tests\test_email_dispatcher.py
.\venv\Scripts\python.exe tests\test_alerts.py
.\venv\Scripts\python.exe tests\test_admin.py
```

Os testes do crawler usam mocks e fixtures. Não execute o crawler geral contra fontes externas como parte da suíte.

### Frontend

Execute a partir de `frontend`:

```powershell
npm ci
npm run lint
npm run build
npm audit
```

### Docker

Execute a partir da raiz. Esses dois comandos podem usar o arquivo de exemplo porque não iniciam a stack:

```powershell
docker compose --env-file .env.prod.example -f docker-compose.prod.yml config --quiet
docker compose --env-file .env.prod.example -f docker-compose.prod.yml build
```

Para uma validação de runtime, use um `.env.prod` sem placeholders, certificado local e um project name exclusivo.

### Smoke

O smoke valida health, readiness, OpenAPI conforme configuração, login administrativo, fontes, status do crawler e listagem de editais. Ele não executa o crawler geral.

Os exemplos de smoke, backup e restauração abaixo usam Windows PowerShell local. Em um servidor Linux com PowerShell 7, substitua `powershell.exe` por `pwsh`.

```powershell
$SmokeSecret = Read-Host "Senha do administrador" -AsSecureString
$env:SMOKE_ADMIN_PASSWORD = [Net.NetworkCredential]::new("", $SmokeSecret).Password
try {
    powershell.exe -NoProfile -File .\scripts\remote-smoke-test.ps1 `
        -EnvFile .\.env.prod `
        -ProjectName monitor-editais-staging
}
finally {
    Remove-Item Env:\SMOKE_ADMIN_PASSWORD -ErrorAction SilentlyContinue
    Remove-Variable SmokeSecret -ErrorAction SilentlyContinue
}
```

No `.env.prod`, `SMOKE_BASE_URL` deve conter somente a origem HTTPS; `SMOKE_API_PREFIX=/api` adiciona o prefixo.

## Crawler e scheduler

A execução manual exige administrador:

- geral: `POST /admin/run-crawler`;
- por fonte: `POST /admin/run-crawler/source/{source_id}`;
- painel: `/admin/crawler`;
- status: `GET /admin/crawler/status`;
- fontes: `GET /admin/crawler/sources-status`;
- histórico: `GET /admin/crawler/runs`.

Sob Nginx, use o prefixo público `/api`. O painel permite acompanhar última checagem, último sucesso, erros, itens encontrados, novos itens e histórico recente.

O scheduler deve permanecer inicialmente com:

```env
CRAWLER_SCHEDULER_ENABLED=false
CRAWLER_INTERVAL_MINUTES=360
UVICORN_WORKERS=1
```

Se for habilitado depois, exatamente um processo e uma instância do backend devem ser responsáveis por ele. `max_instances=1` evita sobreposição dentro de um scheduler, mas não coordena múltiplos processos ou réplicas.

## Backup e restauração

O backup usa formato custom do PostgreSQL e deve ser gravado fora do repositório:

```powershell
$BackupDirectory = Read-Host "Diretório externo para o backup"

powershell.exe -NoProfile -File .\scripts\backup-postgres.ps1 `
    -BackupDirectory $BackupDirectory `
    -EnvFile .\.env.prod `
    -ProjectName monitor-editais-staging
```

Para validar uma restauração, escolha um banco separado, previamente criado e vazio. O script de restauração não cria o banco alvo.

```powershell
$PostgresUser = Read-Host "POSTGRES_USER configurado em .env.prod"
docker compose --env-file .env.prod -f docker-compose.prod.yml exec -T db createdb --username $PostgresUser monitor_editais_restore_test

$BackupPath = Read-Host "Caminho completo do arquivo .dump"

powershell.exe -NoProfile -File .\scripts\restore-postgres.ps1 `
    -BackupPath $BackupPath `
    -TargetDatabase monitor_editais_restore_test `
    -ConfirmDatabase monitor_editais_restore_test `
    -EnvFile .\.env.prod `
    -ProjectName monitor-editais-staging
```

O script recusa restaurar no banco principal configurado. Restaurações devem ocorrer de forma controlada, com banco alvo vazio e `TargetDatabase` e `ConfirmDatabase` idênticos. Não sobrescreva o banco principal sem confirmação explícita, janela operacional e backup previamente conferido.

## Documentação

- [Cobertura nacional auditável](docs/cobertura_nacional.md)
- [Operação do crawler e painel](docs/operacao.md)
- [Checklist de homologação](docs/checklist_homologacao.md)
- [Deploy de homologação remota](docs/deploy_homologacao_remota.md)
- [Auditoria das fontes Nordeste](docs/auditoria_fontes_nordeste.md)
- [Instruções para agentes e contribuidores](AGENTS.md)

## Segurança operacional

- mantenha segredos e arquivos `.env` reais fora do Git;
- mantenha certificados e chaves privadas fora do Git;
- não versione bancos, dumps, backups, logs ou artefatos de build;
- exponha apenas o Nginx; backend e PostgreSQL permanecem internos;
- use TLS válido na homologação pública;
- mantenha OpenAPI conforme a decisão operacional do ambiente;
- mantenha o scheduler desativado até a validação manual;
- quando ativado, use uma única instância responsável;
- armazene backups fora do repositório e teste restaurações em banco separado.

## Status do projeto

Confirmado nesta fase:

- backend, migrations, autenticação, health, readiness, seed, scheduler desativado e suíte Python;
- frontend, lint, build e auditoria de dependências;
- Compose, imagens, PostgreSQL, migration one-shot, Nginx, HTTPS, proxy e fallback SPA;
- administrador, seed nacional idempotente e wrapper Nordeste compatível;
- smoke, backup e restauração em ambiente descartável;
- inventário nacional auditável e manifestos regionais reconciliados; a validação operacional das fontes continua progressiva.

Pendente para uma homologação remota real:

- servidor e acesso remoto;
- DNS;
- certificado público;
- segredos reais;
- configuração SMTP, se necessária;
- execução do deploy e observação operacional.

Não há declaração de produção concluída.

## Licença

Este projeto é disponibilizado sob a Licença de Uso Não Comercial — Monitor de Editais. Consulte [LICENSE.md](LICENSE.md) para os termos completos.
