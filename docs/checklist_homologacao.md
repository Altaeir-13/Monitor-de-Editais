# Checklist de Homologação

Use este checklist antes de considerar o Monitor de Editais pronto para homologação ou produção assistida.

## Ambiente

- [ ] `backend/.env` foi criado a partir de `backend/.env.example`.
- [ ] `frontend/.env` foi criado a partir de `frontend/.env.example`.
- [ ] `SECRET_KEY` foi trocada por valor forte.
- [ ] `DATABASE_URL` aponta para banco correto do ambiente.
- [ ] PostgreSQL está disponível para homologação/produção.
- [ ] SQLite, se usado, está restrito a validação local controlada.
- [ ] `.env` real não está versionado.

## Backend

- [ ] Backend sobe sem erro.
- [ ] Migrations/tabelas estão disponíveis no banco do ambiente.
- [ ] Login admin funciona.
- [ ] `POST /admin/seed-northeast` executa sem duplicar fontes.
- [ ] `POST /admin/run-crawler` executa e retorna resumo.
- [ ] `POST /admin/run-crawler/source/{source_id}` executa uma fonte específica.
- [ ] Falhas externas de fontes não interrompem a execução geral.
- [ ] Scheduler está desativado por padrão.
- [ ] Scheduler só é ativado com `CRAWLER_SCHEDULER_ENABLED=true` em ambiente controlado.

## Frontend

- [ ] Frontend sobe sem erro.
- [ ] Login admin funciona pela interface.
- [ ] `/admin/crawler` abre.
- [ ] Cards de resumo carregam.
- [ ] Tabela de fontes carrega.
- [ ] Histórico recente carrega.
- [ ] Execução por fonte funciona.
- [ ] Execução geral funciona.
- [ ] Link para URL oficial da fonte abre.
- [ ] Link para edição de fontes abre `/admin/sources`.
- [ ] Listagem pública de editais mostra dados.

## Painel Operacional

- [ ] Status `ok` aparece para fontes funcionais.
- [ ] Status `warning` aparece para fontes sem itens no último run.
- [ ] Status `error` aparece para fontes com falha.
- [ ] Status `never_checked` aparece para fontes ainda não checadas.
- [ ] Status `inactive` aparece para fontes desativadas.
- [ ] Última checagem é exibida.
- [ ] Último sucesso é exibido.
- [ ] Último erro é exibido quando houver.
- [ ] Itens encontrados e novos salvos são exibidos.

## Validações Técnicas

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

## Resultado da Validação Manual Registrada

Validação registrada nesta fase:

- Backend: `127.0.0.1:8000`
- Frontend: `127.0.0.1:5173`
- Banco local: `backend/audit_northeast_final.db` ignorado pelo Git
- Admin: `admin.manual@example.com`
- `/admin/crawler`: HTTP 200
- Login admin: OK
- Cards: OK
- Fontes totais: 83
- Fontes ativas: 82
- Editais ativos antes da execução geral: 1.418
- Tabela de fontes: 83 fontes carregadas
- Histórico: 50 runs recentes carregados
- Execução de fonte específica `#78`: OK
- Execução geral: `sources_checked=82`, `items_found=5674`, `new_items=3336`, `failed_sources=4`
- As 4 falhas foram falhas reais de fontes externas, e o runner continuou corretamente.

## Critério de Pronto para Homologação

- [ ] Todos os itens críticos de ambiente foram conferidos.
- [ ] Backend e frontend sobem de forma reproduzível.
- [ ] Admin consegue operar crawler pelo painel.
- [ ] Falhas externas são visíveis no painel e não quebram execução geral.
- [ ] Validações técnicas passaram.
- [ ] Nenhum artefato local ou segredo real está em `git status --short`.