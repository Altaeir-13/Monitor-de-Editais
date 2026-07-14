# Operação do Monitor de Editais

Este guia descreve como operar o crawler e interpretar o painel administrativo `/admin/crawler` em homologação ou produção.

Para validação local rápida do backend, use `backend/.env.local.example`, que aponta para SQLite (`sqlite:///./app.db`) e mantém o scheduler desativado. O arquivo `backend/.env.example` aponta para PostgreSQL e exige PostgreSQL rodando, banco criado e credenciais compatíveis.

## Catálogo e cobertura nacional

O inventário institucional possui alcance nacional. A cobertura operacional das fontes permanece em validação progressiva.

A linha de base usa o Censo da Educação Superior 2024 do Inep com
`NU_ANO_CENSO = 2024` e `TP_REDE = 1`. O inventário auditável tem 320
instituições; 318 formam o alvo elegível. Há 303 fontes no inventário, das quais
302 pertencem a instituições elegíveis. Entre as elegíveis, 263 possuem fonte e
55 ainda não possuem.

Esses números não autorizam execução nacional do crawler. `verified` confirma
a fonte oficial, mas não confirma captura. Captura validada não equivale a
monitoramento contínuo. Nesta versão, captura validada nacional e monitoramento
ativo nacional permanecem em zero.

As rotas administrativas disponíveis sob o prefixo público `/api` são:

- `GET /api/admin/coverage`;
- `GET /api/admin/coverage/regions`;
- `GET /api/admin/coverage/institutions`;
- `POST /api/admin/seed-national`.

As rotas exigem administrador. Fontes criadas pelo seed nacional permanecem
inativas. Mantenha `CRAWLER_SCHEDULER_ENABLED=false` durante seed, homologação
e auditoria amostrada.

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

## Seed nacional e compatibilidade Nordeste

Execute o seed nacional como administrador:

```http
POST /admin/seed-national
```

Sob Nginx, use `POST /api/admin/seed-national`. A execução pode abranger todo o
alvo elegível ou ser filtrada por região. O serviço só inclui registros cujo
`eligibility_status` começa com `included`, preserva registros existentes sem
regra explícita de substituição e cria fontes com `is_active=false`.

O endpoint legado continua disponível:

```http
POST /admin/seed-northeast
```

Ele é um wrapper do seed nacional limitado ao Nordeste. Ambos são idempotentes:
uma segunda execução não duplica instituições nem fontes. Antes de prosseguir,
revise separadamente instituições e fontes criadas, atualizadas e ignoradas,
além das pendências e revisões manuais.

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

## Homologação PostgreSQL

Homologação compartilhada e produção usam PostgreSQL; SQLite fica restrito a
desenvolvimento e testes locais isolados. Prepare um `.env.prod` fora do Git a
partir de `.env.prod.example` e use um project name conhecido:

```powershell
$ProjectName = "monitor-editais-staging"
docker compose --project-name $ProjectName --env-file .env.prod -f docker-compose.prod.yml config --quiet
docker compose --project-name $ProjectName --env-file .env.prod -f docker-compose.prod.yml build
docker compose --project-name $ProjectName --env-file .env.prod -f docker-compose.prod.yml up -d --wait
docker compose --project-name $ProjectName --env-file .env.prod -f docker-compose.prod.yml ps
docker compose --project-name $ProjectName --env-file .env.prod -f docker-compose.prod.yml logs --tail=100 migrate backend frontend
```

As migrations **não** são aplicadas pelo startup do backend. O serviço one-shot
`migrate` executa `alembic upgrade head` e deve terminar com código zero antes
de o backend iniciar. Use `/health` para o processo e `/ready` para confirmar a
conexão com o banco.

Crie o administrador sem expor a senha:

```powershell
docker compose --project-name $ProjectName --env-file .env.prod -f docker-compose.prod.yml exec backend python scripts/create_admin.py --name "Administrador" --email "admin@example.com"
```

Execute o smoke com credenciais fornecidas pelo ambiente ou por prompt, nunca
versionadas. Não registre senhas, tokens, `SECRET_KEY`, credenciais SMTP ou
`DATABASE_URL` com senha em logs ou tickets. Para diagnóstico, registre apenas
status HTTP, contadores e mensagens operacionais sem segredo.

## Validacao controlada do scheduler

Mantenha `CRAWLER_SCHEDULER_ENABLED=false` por padrao. Habilite o scheduler apenas depois de validar manualmente seed, painel e crawler por uma unica fonte.

Para teste controlado em Docker descartavel, use temporariamente:

```env
CRAWLER_SCHEDULER_ENABLED=true
CRAWLER_INTERVAL_MINUTES=1
```

Regras operacionais:

- execute apenas uma instancia do backend quando o scheduler estiver habilitado;
- nao rode multiplos workers ou replicas com scheduler ativo, porque cada processo pode iniciar seu proprio APScheduler;
- confirme nos logs `Crawler scheduler job registered`, `Crawler scheduler started`, `Scheduled crawler started`, `Scheduled crawler completed` ou `Scheduled crawler failed`;
- em caso de comportamento inesperado, volte `CRAWLER_SCHEDULER_ENABLED=false` e recrie o backend;
- o job usa `max_instances=1` e `coalesce=True` para evitar sobreposicao dentro do mesmo processo.

## Auditoria nacional amostrada

A auditoria nacional é pequena e controlada: selecione ao menos uma instituição
por região, varie os tipos de spider e inclua fontes `verified` e `partial`.
Use concorrência baixa, timeout, User-Agent identificável e respeito a
`robots.txt`. Não autentique, não contorne bloqueios e não ative fontes.

Registre amostra, horário, parâmetros, respostas e limitações. Um resultado
amostral não demonstra cobertura operacional nacional e não autoriza o crawler
geral nem a habilitação permanente do scheduler.

## Operacao da homologacao remota

Use `docs/deploy_homologacao_remota.md` como fonte canonica para a stack
remota. O guia cobre HTTPS de mesma origem, variaveis, migrations, admin, seed,
smoke, logs, backup, restore, rollback e scheduler.

Comandos operacionais devem informar `--env-file`, `-f` e um project name
conhecido. Nao execute `docker compose config` sem `--quiet` com segredos e
nao use `down -v` fora de ambiente descartavel criado pela mesma tarefa.
