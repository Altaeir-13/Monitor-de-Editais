# Checklist de Homologação

Use este checklist antes de considerar o Monitor de Editais pronto para homologação ou produção assistida.

## Expansão nacional auditável

- [ ] A formulação de transparência está visível: “O inventário institucional possui alcance nacional. A cobertura operacional das fontes permanece em validação progressiva.”
- [ ] A base canônica é o Censo da Educação Superior 2024 do Inep.
- [ ] O gerador aplica `NU_ANO_CENSO = 2024` e `TP_REDE = 1`.
- [ ] O checksum SHA-256 do CSV canônico é `aaa37fb9433d005686616bb9e48c5d7083526fdcc171973e787eed35a2ee349d`.
- [ ] Totais conferidos: 317 registros públicos, 315 elegíveis no Censo e 3 instituições pós-Censo.
- [ ] Inventário conferido: 320 registros, 318 elegíveis e 2 excluídos preservados.
- [ ] Fontes conferidas: 303 no inventário, 302 elegíveis e 1 histórica excluída.
- [ ] Instituições elegíveis conferidas: 263 com fonte e 55 sem fonte.
- [ ] Status conferidos: 93 `verified`, 165 `partial`, 29 `manual_review` e 31 `source_not_found`.
- [ ] Captura validada nacional permanece 0 enquanto não houver evidência.
- [ ] Monitoramento ativo nacional permanece 0 enquanto não houver evidência.
- [ ] Totais regionais elegível/com fonte/fontes: CO 29/27/27, NE 67/46/85, N 24/24/24, SE 166/134/134 e S 32/32/32.
- [ ] O inventário Sul mostra 34 registros: UNC em revisão de escopo e UNIUV inativa continuam auditáveis.
- [ ] A única fonte histórica da UNIUV está inativa e fora das 302 fontes elegíveis.
- [ ] Inventário, fonte mapeada, `verified`, captura validada e monitoramento ativo aparecem como estágios distintos.
- [ ] Nenhuma tela ou documento confunde inventário nacional com operação validada em todo o país.
- [ ] Fontes criadas pelo seed nacional permanecem inativas.
- [ ] `CRAWLER_SCHEDULER_ENABLED=false` permanece o padrão remoto.

## Catálogo e seed

- [ ] `test_national_catalog.py`, `test_source_manifests.py` e `test_catalog_eligibility.py` passaram.
- [ ] O seed nacional inclui somente `eligibility_status` iniciado por `included`.
- [ ] `POST /api/admin/seed-national` exige administrador.
- [ ] O seed nacional completo foi executado duas vezes sem duplicação.
- [ ] O seed filtrado por região foi validado.
- [ ] O wrapper `POST /api/admin/seed-northeast` continua compatível.
- [ ] Instituições e fontes criadas, atualizadas e ignoradas foram conferidas separadamente.
- [ ] Pendências e revisões manuais foram conferidas.

## Cobertura administrativa

- [ ] `GET /api/admin/coverage` exige administrador e retorna totais coerentes.
- [ ] `GET /api/admin/coverage/regions` retorna a distribuição regional.
- [ ] `GET /api/admin/coverage/institutions` retorna lista e filtros.
- [ ] Filtros de região, UF, categoria, organização, elegibilidade, cobertura, verificação, ativação e presença de fonte foram testados.
- [ ] O painel explica que fonte verificada não significa captura validada.
- [ ] O painel explica que captura validada não significa monitoramento contínuo.

## Migrations e bancos descartáveis

SQLite:

- [ ] Um banco SQLite temporário isolado foi selecionado antes de importar as configurações.
- [ ] `alembic upgrade head` passou.
- [ ] O downgrade da migration nacional passou.
- [ ] Um novo `alembic upgrade head` passou.
- [ ] Leitura e escrita dos campos nacionais passaram.
- [ ] Seed repetido e filtro regional passaram.

PostgreSQL:

- [ ] Um project name e um volume exclusivos desta validação foram registrados.
- [ ] Upgrade até head, downgrade da migration nacional e novo upgrade passaram.
- [ ] Seed nacional e repetição idempotente passaram.
- [ ] Filtros e API de cobertura passaram.
- [ ] Somente recursos criados nesta validação foram removidos.

## Docker e frontend

- [ ] `docker compose --env-file .env.prod.example -f docker-compose.prod.yml config --quiet` passou.
- [ ] `docker compose --env-file .env.prod.example -f docker-compose.prod.yml build` passou.
- [ ] Em runtime descartável, Nginx foi o único serviço com portas públicas.
- [ ] Backend e PostgreSQL ficaram sem host port bindings.
- [ ] O serviço one-shot `migrate` terminou com código zero antes do backend.
- [ ] `npm ci`, lint, build e audit foram executados dentro de `frontend`.
- [ ] `npm audit` reportou zero vulnerabilidades conhecidas ou qualquer falha foi registrada sem `--force`.
- [ ] Nenhum `package.json`, `node_modules` ou `dist` foi criado na raiz.

## Auditoria amostrada

- [ ] A amostra inclui ao menos uma instituição de cada região.
- [ ] A amostra varia spiders e inclui fontes `verified` e `partial`.
- [ ] Concorrência, timeout e User-Agent identificável foram registrados.
- [ ] `robots.txt` foi respeitado quando aplicável.
- [ ] Não houve autenticação, bypass, ativação de fonte ou crawler nacional completo.
- [ ] O resultado foi descrito como amostral, sem inferência nacional.

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

## Checklist de Homologacao PostgreSQL Reproduzivel

- [ ] A branch de trabalho atual foi conferida, sem impor um nome legado fixo.
- [ ] `git status --short` limpo antes das alteracoes.
- [ ] `.env` criado a partir de `.env.prod.example` e nao versionado.
- [ ] `POSTGRES_PASSWORD` real definido somente no `.env` local/ambiente.
- [ ] `SECRET_KEY` real, longo e diferente do placeholder.
- [ ] `CRAWLER_SCHEDULER_ENABLED=false` na primeira rodada.
- [ ] `docker compose -f docker-compose.prod.yml config` passou.
- [ ] `docker compose -f docker-compose.prod.yml build` passou.
- [ ] PostgreSQL subiu saudavel pelo health check.
- [ ] O serviço one-shot `migrate` aplicou `alembic upgrade head` e terminou com código zero antes do backend.
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
- [ ] Validação Docker foi feita em banco descartável e somente o volume criado para o project name registrado foi removido.
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
