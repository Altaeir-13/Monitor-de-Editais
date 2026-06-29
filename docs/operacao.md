# Operação do Monitor de Editais

Este guia descreve como operar o crawler e interpretar o painel administrativo `/admin/crawler` em homologação ou produção.

Para validação local rápida do backend, use `backend/.env.local.example`, que aponta para SQLite (`sqlite:///./app.db`) e mantém o scheduler desativado. O arquivo `backend/.env.example` aponta para PostgreSQL e exige PostgreSQL rodando, banco criado e credenciais compatíveis.

## Painel Operacional do Crawler

Acesse como usuário admin:

```text
/admin/crawler
```

O painel mostra:

- resumo geral das fontes;
- tabela de status por fonte;
- histórico recente de execuções;
- execução manual geral;
- execução manual de uma fonte específica;
- atalhos para abrir URL oficial e acessar edição de fontes.

## Status das Fontes

- `ok`: fonte ativa com último run bem-sucedido e itens encontrados.
- `warning`: fonte ativa com último run concluído, mas sem itens encontrados.
- `error`: último run falhou ou a fonte possui `last_error_message`.
- `never_checked`: fonte ativa sem checagem ou histórico de execução.
- `inactive`: fonte desativada; não será executada pelo crawler.

`warning` não significa necessariamente erro. Pode indicar uma fonte válida sem edital novo no momento.

## Execução Geral

Use o botão de execução geral no painel ou o endpoint:

```http
POST /admin/run-crawler
```

A execução geral percorre as fontes ativas. Falhas individuais são registradas, mas não devem interromper o restante do crawler.

## Execução por Fonte

Use o botão de execução na linha da fonte ou o endpoint:

```http
POST /admin/run-crawler/source/{source_id}
```

Essa ação é indicada para:

- validar uma correção de fonte;
- investigar uma fonte com erro;
- evitar rodar todas as fontes durante uma análise pontual.

## Investigação de Fonte com Erro

1. Abra `/admin/crawler`.
2. Localize fontes com status `error`.
3. Leia a coluna de último erro.
4. Abra a URL oficial da fonte.
5. Reexecute apenas a fonte.
6. Se o erro persistir, classifique a causa antes de alterar o crawler.

## Erro Externo vs Erro do Sistema

Normalmente é erro externo quando ocorrer:

- certificado SSL expirado, inválido ou self-signed;
- conexão resetada pelo host remoto;
- timeout em portal oficial;
- HTTP 404 em página institucional;
- redirecionamento para login, captcha ou sessão;
- indisponibilidade temporária do site.

Normalmente é erro do sistema quando ocorrer:

- traceback de código sem relação com rede externa;
- erro de banco de dados;
- falha de importação ou configuração local;
- erro de normalização/persistência em dados válidos;
- falha em todos os spiders após mudança de código.

Erros externos devem ser documentados e acompanhados. Não desative uma fonte oficial sem evidência de que ela foi substituída por outra fonte oficial melhor.

## Histórico de Execuções

O histórico usa `CrawlerRun`, que representa execução por fonte. Ele mostra:

- fonte executada;
- instituição;
- status;
- itens encontrados;
- novos editais salvos;
- erro, quando houver;
- início e fim da execução.

O painel não usa uma tabela de execução geral. O resumo geral é calculado por agregação de fontes, runs e editais.

## Scheduler

O scheduler fica desativado por padrão:

```env
CRAWLER_SCHEDULER_ENABLED=false
CRAWLER_INTERVAL_MINUTES=360
```

Ative apenas em ambiente controlado:

```env
CRAWLER_SCHEDULER_ENABLED=true
CRAWLER_INTERVAL_MINUTES=360
```

Para verificar se está ativo:

- confira as variáveis de ambiente do backend;
- confira os logs de inicialização da aplicação;
- procure logs de início, conclusão ou falha do job agendado.

## Seed Nordeste

Execute como admin:

```http
POST /admin/seed-northeast
```

O seed é idempotente. A segunda execução não deve duplicar instituições ou fontes. Fontes antigas listadas em `replaces` devem ser atualizadas/substituídas de forma segura.

## Arquivos que Nunca Devem Ser Versionados

- `.env` reais;
- `venv/`;
- `node_modules/`;
- `dist/`;
- `__pycache__/`;
- `*.pyc`;
- bancos SQLite locais: `*.db`, `*.sqlite`, `*.sqlite3`;
- bancos temporários de auditoria;
- arquivos temporários de validação.

## Validação Manual Registrada

Última validação manual registrada nesta fase:

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