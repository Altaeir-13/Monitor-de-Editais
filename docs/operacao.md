# OperaÃƒÂ§ÃƒÂ£o do Monitor de Editais

Este guia descreve como operar o crawler e interpretar o painel administrativo `/admin/crawler` em homologaÃƒÂ§ÃƒÂ£o ou produÃƒÂ§ÃƒÂ£o.

Para validaÃƒÂ§ÃƒÂ£o local rÃƒÂ¡pida do backend, use `backend/.env.local.example`, que aponta para SQLite (`sqlite:///./app.db`) e mantÃƒÂ©m o scheduler desativado. O arquivo `backend/.env.example` aponta para PostgreSQL e exige PostgreSQL rodando, banco criado e credenciais compatÃƒÂ­veis.

## Painel Operacional do Crawler

Acesse como usuÃƒÂ¡rio admin:

```text
/admin/crawler
```

O painel mostra:

- resumo geral das fontes;
- tabela de status por fonte;
- histÃƒÂ³rico recente de execuÃƒÂ§ÃƒÂµes;
- execuÃƒÂ§ÃƒÂ£o manual geral;
- execuÃƒÂ§ÃƒÂ£o manual de uma fonte especÃƒÂ­fica;
- atalhos para abrir URL oficial e acessar ediÃƒÂ§ÃƒÂ£o de fontes.

## Status das Fontes

- `ok`: fonte ativa com ÃƒÂºltimo run bem-sucedido e itens encontrados.
- `warning`: fonte ativa com ÃƒÂºltimo run concluÃƒÂ­do, mas sem itens encontrados.
- `error`: ÃƒÂºltimo run falhou ou a fonte possui `last_error_message`.
- `never_checked`: fonte ativa sem checagem ou histÃƒÂ³rico de execuÃƒÂ§ÃƒÂ£o.
- `inactive`: fonte desativada; nÃƒÂ£o serÃƒÂ¡ executada pelo crawler.

`warning` nÃƒÂ£o significa necessariamente erro. Pode indicar uma fonte vÃƒÂ¡lida sem edital novo no momento.

## ExecuÃƒÂ§ÃƒÂ£o Geral

Use o botÃƒÂ£o de execuÃƒÂ§ÃƒÂ£o geral no painel ou o endpoint:

```http
POST /admin/run-crawler
```

A execuÃƒÂ§ÃƒÂ£o geral percorre as fontes ativas. Falhas individuais sÃƒÂ£o registradas, mas nÃƒÂ£o devem interromper o restante do crawler.

## ExecuÃƒÂ§ÃƒÂ£o por Fonte

Use o botÃƒÂ£o de execuÃƒÂ§ÃƒÂ£o na linha da fonte ou o endpoint:

```http
POST /admin/run-crawler/source/{source_id}
```

Essa aÃƒÂ§ÃƒÂ£o ÃƒÂ© indicada para:

- validar uma correÃƒÂ§ÃƒÂ£o de fonte;
- investigar uma fonte com erro;
- evitar rodar todas as fontes durante uma anÃƒÂ¡lise pontual.

## InvestigaÃƒÂ§ÃƒÂ£o de Fonte com Erro

1. Abra `/admin/crawler`.
2. Localize fontes com status `error`.
3. Leia a coluna de ÃƒÂºltimo erro.
4. Abra a URL oficial da fonte.
5. Reexecute apenas a fonte.
6. Se o erro persistir, classifique a causa antes de alterar o crawler.

## Erro Externo vs Erro do Sistema

Normalmente ÃƒÂ© erro externo quando ocorrer:

- certificado SSL expirado, invÃƒÂ¡lido ou self-signed;
- conexÃƒÂ£o resetada pelo host remoto;
- timeout em portal oficial;
- HTTP 404 em pÃƒÂ¡gina institucional;
- redirecionamento para login, captcha ou sessÃƒÂ£o;
- indisponibilidade temporÃƒÂ¡ria do site.

Normalmente ÃƒÂ© erro do sistema quando ocorrer:

- traceback de cÃƒÂ³digo sem relaÃƒÂ§ÃƒÂ£o com rede externa;
- erro de banco de dados;
- falha de importaÃƒÂ§ÃƒÂ£o ou configuraÃƒÂ§ÃƒÂ£o local;
- erro de normalizaÃƒÂ§ÃƒÂ£o/persistÃƒÂªncia em dados vÃƒÂ¡lidos;
- falha em todos os spiders apÃƒÂ³s mudanÃƒÂ§a de cÃƒÂ³digo.

Erros externos devem ser documentados e acompanhados. NÃƒÂ£o desative uma fonte oficial sem evidÃƒÂªncia de que ela foi substituÃƒÂ­da por outra fonte oficial melhor.

## HistÃƒÂ³rico de ExecuÃƒÂ§ÃƒÂµes

O histÃƒÂ³rico usa `CrawlerRun`, que representa execuÃƒÂ§ÃƒÂ£o por fonte. Ele mostra:

- fonte executada;
- instituiÃƒÂ§ÃƒÂ£o;
- status;
- itens encontrados;
- novos editais salvos;
- erro, quando houver;
- inÃƒÂ­cio e fim da execuÃƒÂ§ÃƒÂ£o.

O painel nÃƒÂ£o usa uma tabela de execuÃƒÂ§ÃƒÂ£o geral. O resumo geral ÃƒÂ© calculado por agregaÃƒÂ§ÃƒÂ£o de fontes, runs e editais.

## Scheduler

O scheduler fica desativado por padrÃƒÂ£o:

```env
CRAWLER_SCHEDULER_ENABLED=false
CRAWLER_INTERVAL_MINUTES=360
```

Ative apenas em ambiente controlado:

```env
CRAWLER_SCHEDULER_ENABLED=true
CRAWLER_INTERVAL_MINUTES=360
```

Para verificar se estÃƒÂ¡ ativo:

- confira as variÃƒÂ¡veis de ambiente do backend;
- confira os logs de inicializaÃƒÂ§ÃƒÂ£o da aplicaÃƒÂ§ÃƒÂ£o;
- procure logs de inÃƒÂ­cio, conclusÃƒÂ£o ou falha do job agendado.

## Seed Nordeste

Execute como admin:

```http
POST /admin/seed-northeast
```

O seed ÃƒÂ© idempotente. A segunda execuÃƒÂ§ÃƒÂ£o nÃƒÂ£o deve duplicar instituiÃƒÂ§ÃƒÂµes ou fontes. Fontes antigas listadas em `replaces` devem ser atualizadas/substituÃƒÂ­das de forma segura.

## Arquivos que Nunca Devem Ser Versionados

- `.env` reais;
- `venv/`;
- `node_modules/`;
- `dist/`;
- `__pycache__/`;
- `*.pyc`;
- bancos SQLite locais: `*.db`, `*.sqlite`, `*.sqlite3`;
- bancos temporÃƒÂ¡rios de auditoria;
- arquivos temporÃƒÂ¡rios de validaÃƒÂ§ÃƒÂ£o.

## ValidaÃƒÂ§ÃƒÂ£o Manual Registrada

ÃƒÅ¡ltima validaÃƒÂ§ÃƒÂ£o manual registrada nesta fase:

- Backend: `127.0.0.1:8000`
- Frontend: `127.0.0.1:5173`
- Banco local: `backend/audit_northeast_final.db` ignorado pelo Git
- Admin: `admin.manual@example.com`
- `/admin/crawler`: HTTP 200
- Login admin: OK
- Cards: OK
- Fontes totais: 83
- Fontes ativas: 82
- Editais ativos antes da execuÃƒÂ§ÃƒÂ£o geral: 1.418
- Tabela de fontes: 83 fontes carregadas
- HistÃƒÂ³rico: 50 runs recentes carregados
- ExecuÃƒÂ§ÃƒÂ£o de fonte especÃƒÂ­fica `#78`: OK
- ExecuÃƒÂ§ÃƒÂ£o geral: `sources_checked=82`, `items_found=5674`, `new_items=3336`, `failed_sources=4`
- As 4 falhas foram falhas reais de fontes externas, e o runner continuou corretamente.

## Homologacao PostgreSQL

Para homologacao, use PostgreSQL via `docker-compose.prod.yml`; nao use SQLite. O arquivo `.env.prod.example` define placeholders seguros e deve ser copiado para `.env` antes da subida.

Sequencia recomendada:

```powershell
cd "C:\Users\Altair\Documents\Working\Development\Monitor de Editais"
copy .env.prod.example .env
notepad .env
docker compose -f docker-compose.prod.yml config
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d db
docker compose -f docker-compose.prod.yml up -d backend frontend
```

O backend aplica migrations no startup. Use `/health` para processo vivo e `/ready` para confirmar banco acessivel.

Crie o admin com:

```powershell
docker compose -f docker-compose.prod.yml exec backend python scripts/create_admin.py --name "Administrador" --email "admin@example.com"
```

Execute smoke test com credenciais via variaveis:

```powershell
$env:SMOKE_BASE_URL = "http://localhost/api"
$env:SMOKE_ADMIN_EMAIL = "admin@example.com"
$env:SMOKE_ADMIN_PASSWORD = Read-Host "Senha admin"
docker compose -f docker-compose.prod.yml exec -e SMOKE_BASE_URL=$env:SMOKE_BASE_URL -e SMOKE_ADMIN_EMAIL=$env:SMOKE_ADMIN_EMAIL -e SMOKE_ADMIN_PASSWORD=$env:SMOKE_ADMIN_PASSWORD backend python scripts/smoke_test.py
Remove-Item Env:\SMOKE_BASE_URL
Remove-Item Env:\SMOKE_ADMIN_EMAIL
Remove-Item Env:\SMOKE_ADMIN_PASSWORD
```

Nao registre senhas, tokens, `SECRET_KEY`, credenciais SMTP ou `DATABASE_URL` com senha em logs ou tickets. Para diagnostico, registre apenas status HTTP, contadores e mensagens operacionais sem segredo.
