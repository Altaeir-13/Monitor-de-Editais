# Checklist de HomologaÃ§Ã£o

Use este checklist antes de considerar o Monitor de Editais pronto para homologaÃ§Ã£o ou produÃ§Ã£o assistida.

## Ambiente

- [ ] `backend/.env` foi criado a partir de `backend/.env.example`.
- [ ] `frontend/.env` foi criado a partir de `frontend/.env.example`.
- [ ] `SECRET_KEY` foi trocada por valor forte.
- [ ] `DATABASE_URL` aponta para banco correto do ambiente.
- [ ] PostgreSQL estÃ¡ disponÃ­vel para homologaÃ§Ã£o/produÃ§Ã£o.
- [ ] SQLite, se usado, estÃ¡ restrito a validaÃ§Ã£o local controlada.
- [ ] `.env` real nÃ£o estÃ¡ versionado.

## Backend

- [ ] Backend sobe sem erro.
- [ ] Migrations/tabelas estÃ£o disponÃ­veis no banco do ambiente.
- [ ] Login admin funciona.
- [ ] `POST /admin/seed-northeast` executa sem duplicar fontes.
- [ ] `POST /admin/run-crawler` executa e retorna resumo.
- [ ] `POST /admin/run-crawler/source/{source_id}` executa uma fonte especÃ­fica.
- [ ] Falhas externas de fontes nÃ£o interrompem a execuÃ§Ã£o geral.
- [ ] Scheduler estÃ¡ desativado por padrÃ£o.
- [ ] Scheduler sÃ³ Ã© ativado com `CRAWLER_SCHEDULER_ENABLED=true` em ambiente controlado.

## Frontend

- [ ] Frontend sobe sem erro.
- [ ] Login admin funciona pela interface.
- [ ] `/admin/crawler` abre.
- [ ] Cards de resumo carregam.
- [ ] Tabela de fontes carrega.
- [ ] HistÃ³rico recente carrega.
- [ ] ExecuÃ§Ã£o por fonte funciona.
- [ ] ExecuÃ§Ã£o geral funciona.
- [ ] Link para URL oficial da fonte abre.
- [ ] Link para ediÃ§Ã£o de fontes abre `/admin/sources`.
- [ ] Listagem pÃºblica de editais mostra dados.

## Painel Operacional

- [ ] Status `ok` aparece para fontes funcionais.
- [ ] Status `warning` aparece para fontes sem itens no Ãºltimo run.
- [ ] Status `error` aparece para fontes com falha.
- [ ] Status `never_checked` aparece para fontes ainda nÃ£o checadas.
- [ ] Status `inactive` aparece para fontes desativadas.
- [ ] Ãšltima checagem Ã© exibida.
- [ ] Ãšltimo sucesso Ã© exibido.
- [ ] Ãšltimo erro Ã© exibido quando houver.
- [ ] Itens encontrados e novos salvos sÃ£o exibidos.

## ValidaÃ§Ãµes TÃ©cnicas

Backend:

```powershell
cd backend
venv\Scripts\python.exe tests\test_crawler.py
```

- [ ] `test_crawler.py` passou.

Frontend:

```powershell
cd frontend
npm run lint
npm run build
```

- [ ] `npm run lint` passou.
- [ ] `npm run build` passou.

## Resultado da ValidaÃ§Ã£o Manual Registrada

ValidaÃ§Ã£o registrada nesta fase:

- Backend: `127.0.0.1:8000`
- Frontend: `127.0.0.1:5173`
- Banco local: `backend/audit_northeast_final.db` ignorado pelo Git
- Admin: `admin.manual@example.com`
- `/admin/crawler`: HTTP 200
- Login admin: OK
- Cards: OK
- Fontes totais: 83
- Fontes ativas: 82
- Editais ativos antes da execuÃ§Ã£o geral: 1.418
- Tabela de fontes: 83 fontes carregadas
- HistÃ³rico: 50 runs recentes carregados
- ExecuÃ§Ã£o de fonte especÃ­fica `#78`: OK
- ExecuÃ§Ã£o geral: `sources_checked=82`, `items_found=5674`, `new_items=3336`, `failed_sources=4`
- As 4 falhas foram falhas reais de fontes externas, e o runner continuou corretamente.

## CritÃ©rio de Pronto para HomologaÃ§Ã£o

- [ ] Todos os itens crÃ­ticos de ambiente foram conferidos.
- [ ] Backend e frontend sobem de forma reproduzÃ­vel.
- [ ] Admin consegue operar crawler pelo painel.
- [ ] Falhas externas sÃ£o visÃ­veis no painel e nÃ£o quebram execuÃ§Ã£o geral.
- [ ] ValidaÃ§Ãµes tÃ©cnicas passaram.
- [ ] Nenhum artefato local ou segredo real estÃ¡ em `git status --short`.

## Checklist de Homologacao PostgreSQL Reproduzivel

- [ ] Branch usada: `chore/remote-staging-deployment`.
- [ ] `git status --short` limpo antes das alteracoes.
- [ ] `.env` criado a partir de `.env.prod.example` e nao versionado.
- [ ] `POSTGRES_PASSWORD` real definido somente no `.env` local/ambiente.
- [ ] `SECRET_KEY` real, longo e diferente do placeholder.
- [ ] `CRAWLER_SCHEDULER_ENABLED=false` na primeira rodada.
- [ ] `docker compose -f docker-compose.prod.yml config` passou.
- [ ] `docker compose -f docker-compose.prod.yml build` passou.
- [ ] PostgreSQL subiu saudavel pelo health check.
- [ ] Backend subiu e aplicou `alembic upgrade head` sem erro.
- [ ] Frontend serviu build de producao via Nginx.
- [ ] `GET /health` retornou `{"status":"ok"}`.
- [ ] `GET /ready` retornou `{"status":"ok"}`.
- [ ] Admin criado com `python scripts/create_admin.py` sem expor senha.
- [ ] Smoke test passou com `python scripts/smoke_test.py`.
- [ ] Login admin funcionou.
- [ ] `POST /admin/seed-northeast` primeira execucao registrou criacao/atualizacao.
- [ ] `POST /admin/seed-northeast` segunda execucao nao duplicou registros.
- [ ] `/admin/sources` abriu e listou fontes.
- [ ] `/admin/crawler` abriu e exibiu status operacional.
- [ ] Crawler por uma fonte ativa executou e registrou historico.
- [ ] Crawler geral foi executado manualmente apenas apos validar uma fonte.
- [ ] Listagem publica de editais abriu.
- [ ] Usuario comum conseguiu cadastro e login.
- [ ] Filtros por tipo de edital funcionaram.
- [ ] Logs nao expuseram senhas, tokens, `SECRET_KEY`, SMTP ou URL do banco com senha.
- [ ] `npm audit` foi executado e vulnerabilidades foram documentadas sem `npm audit fix --force`.
- [ ] Backup basico testado ou comando registrado.
- [ ] Scheduler testado somente depois da validacao manual, com uma unica instancia do backend.

Registre os numeros desta homologacao:

```text
Instituicoes:
Fontes:
Fontes ativas:
Fontes verificadas:
Itens encontrados:
Novos itens:
Fontes com falha:
Editais salvos:
```

## Checklist de Validacao do Scheduler

- [ ] `CRAWLER_SCHEDULER_ENABLED=false` continua sendo o padrao nos arquivos de exemplo.
- [ ] Teste automatizado confirma que scheduler desativado nao registra job.
- [ ] Teste automatizado confirma um unico job com `max_instances=1` e `coalesce=True`.
- [ ] Teste automatizado confirma que falha do crawler e registrada e nao escapa do job.
- [ ] Teste automatizado confirma fechamento da sessao de banco no `finally`.
- [ ] Teste automatizado confirma shutdown idempotente.
- [ ] Validacao Docker foi feita em banco descartavel e encerrada com remocao do volume.
- [ ] Scheduler habilitado somente com uma instancia do backend.

## Checklist de homologacao remota HTTPS

### Antes do deploy

- [ ] Branch local e `git status --short` foram conferidos.
- [ ] Dominio real foi definido e DNS A/AAAA aponta para o servidor correto.
- [ ] Somente portas 80 e 443 estao publicas para a aplicacao.
- [ ] `.env.prod` nao esta versionado e nao contem placeholders.
- [ ] `SECRET_KEY` e senha PostgreSQL sao valores aleatorios.
- [ ] CORS contem apenas a origem HTTPS esperada e `API_ROOT_PATH=/api`.
- [ ] OpenAPI corresponde a decisao operacional.
- [ ] Scheduler esta false, intervalo 360 e worker igual a um.
- [ ] Diretorio TLS externo contem `fullchain.pem` e `privkey.pem`.

### Compose e runtime

- [ ] `config --quiet` e builds passaram.
- [ ] `migrate` terminou zero e esta em Alembic head.
- [ ] Backend e PostgreSQL nao possuem port binding.
- [ ] Volume PostgreSQL e persistente e project-scoped.
- [ ] Rede `data` e interna.
- [ ] HTTP redireciona para HTTPS.
- [ ] Health/readiness funcionam na raiz e em `/api`.
- [ ] `/api` nunca retorna `index.html`.
- [ ] Refresh de rota SPA profunda funciona.
- [ ] Headers operacionais aparecem nas respostas HTTPS.

### Aplicacao e operacao

- [ ] Admin foi criado/promovido sem senha na saida.
- [ ] Seed foi executado duas vezes sem aumentar contagens.
- [ ] Smoke remoto passou sem executar crawler.
- [ ] Logs foram revisados sem segredos.
- [ ] Backup externo timestampado foi criado.
- [ ] Restore foi validado em banco controlado.
- [ ] Rollback e commit/imagem anterior foram registrados.

### Validacao local

- [ ] Testes backend obrigatorios e novos passaram.
- [ ] `npm ci`, lint, build e audit passaram dentro de `frontend`.
- [ ] Compose config/build e ambiente descartavel passaram.
- [ ] `git diff --check`, status e diff stat passaram.
- [ ] Nenhum env, certificado, banco, dump ou backup apareceu no Git.
