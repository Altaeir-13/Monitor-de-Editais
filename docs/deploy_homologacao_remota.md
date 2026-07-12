# Homologacao remota

Este e o guia canonico para preparar e operar a homologacao remota do Monitor de
Editais. Ele nao executa acesso SSH, DNS, emissao de certificado, commit ou push.

## Topologia

```text
Internet
   |
HTTP 80 -> redirect HTTPS
   |
HTTPS 443
   |
Nginx (frontend build + proxy)
   |
   +-- /              -> SPA React
   +-- /api/*         -> FastAPI
   +-- /health        -> FastAPI liveness
   +-- /ready         -> FastAPI readiness
                          |
                          +-- PostgreSQL interno
```

Somente o servico `frontend` publica portas. `backend` e `db` nao possuem
bindings no host. A rede `data` e interna e liga apenas backend/migration ao
PostgreSQL. A rede `edge` liga Nginx ao backend e preserva egress do crawler.

## Dados que o operador deve fornecer

- dominio real de homologacao;
- registros DNS A e, quando aplicavel, AAAA;
- certificado e chave privada para o dominio;
- senha PostgreSQL aleatoria e URL-safe;
- `SECRET_KEY` aleatoria com pelo menos 32 caracteres;
- e-mail do administrador;
- senha inicial do administrador fornecida apenas pelo ambiente do processo;
- configuracao SMTP, quando o envio de e-mail for validado.

Nao grave valores reais no Git.

## Preparar o servidor

Requisitos locais no servidor:

- Docker Engine;
- Docker Compose v2.20 ou mais recente;
- PowerShell 7 para os scripts `.ps1`;
- portas TCP 80 e 443 liberadas para o Nginx;
- diretorio externo persistente para certificados;
- diretorio externo persistente para backups.

Copie o exemplo e edite o arquivo ignorado:

```powershell
Copy-Item .env.prod.example .env.prod
```

Substitua todos os placeholders. O deploy rejeita `change-me`, dominio
`example.*`, segredo curto, CORS diferente da origem HTTPS, scheduler ativo e
mais de um worker.

Variaveis essenciais:

```env
STAGING_DOMAIN=staging.seu-dominio.tld
TLS_CERT_DIRECTORY=/etc/monitor-editais/tls
POSTGRES_PASSWORD=valor-aleatorio-url-safe
SECRET_KEY=valor-aleatorio-com-32-ou-mais-caracteres
BACKEND_CORS_ORIGINS=["https://staging.seu-dominio.tld"]
API_ROOT_PATH=/api
OPENAPI_ENABLED=false
UVICORN_WORKERS=1
CRAWLER_SCHEDULER_ENABLED=false
CRAWLER_INTERVAL_MINUTES=360
```

O diretorio TLS deve conter `fullchain.pem` e `privkey.pem`. A emissao e a
renovacao do certificado sao gates manuais. Apos renovar, valide e recarregue:

```powershell
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml exec frontend nginx -t
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml exec frontend nginx -s reload
```

## Validar e implantar futuramente

O script valida variaveis e certificados, renderiza o Compose sem imprimir a
configuracao expandida, constroi imagens, executa migration one-shot e aguarda
health checks:

```powershell
pwsh -File scripts/deploy.ps1 -EnvFile .env.prod -ProjectName monitor-editais-staging
```

Equivalentes para inspecao manual:

```powershell
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml config --quiet
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml build
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml up -d --wait
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml ps
```

Nao use `docker compose config` sem `--quiet` com segredos: a saida expandida
pode conter a URL do banco.

## Migrations

O servico `migrate` executa `alembic upgrade head` antes do backend. Reiniciar
o backend nao reaplica migrations.

```powershell
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml ps -a migrate
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml run --rm migrate current
```

Nao execute downgrade automatico. Mudancas destrutivas exigem backup validado e
plano especifico.

## Criar administrador

Forneca a senha apenas ao processo e remova-a ao terminar:

```powershell
try {
    $env:ADMIN_PASSWORD = Read-Host "Senha inicial do admin" -MaskInput
    docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml exec -T -e ADMIN_PASSWORD backend python scripts/create_admin.py --name "Administrador" --email "admin@seu-dominio.tld"
}
finally {
    Remove-Item Env:ADMIN_PASSWORD -ErrorAction SilentlyContinue
}
```

O script e idempotente: cria, promove ou reativa sem duplicar.

## Seed

Depois do login admin, execute `POST /api/admin/seed-northeast` pela interface
ou cliente HTTP controlado. Execute duas vezes e confirme que as contagens nao
aumentam na segunda chamada. O seed nao habilita scheduler nem executa crawler.

## Smoke remoto

O smoke recebe a origem publica e acrescenta `/api`. A senha e o token nao
aparecem na saida.

```powershell
try {
    $env:SMOKE_ADMIN_PASSWORD = Read-Host "Senha do admin" -MaskInput
    pwsh -File scripts/remote-smoke-test.ps1 -EnvFile .env.prod -ProjectName monitor-editais-staging
}
finally {
    Remove-Item Env:SMOKE_ADMIN_PASSWORD -ErrorAction SilentlyContinue
}
```

Ele valida health, readiness, OpenAPI quando habilitado, login admin, fontes,
status do crawler e listagem publica. Ele nunca dispara crawler.

## Logs

```powershell
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml logs --tail 200 backend
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml logs --tail 200 frontend
docker compose --project-name monitor-editais-staging --env-file .env.prod -f docker-compose.prod.yml logs --tail 200 db
```

Nao registre `SECRET_KEY`, senhas, JWT, `DATABASE_URL` ou o conteudo do env.

## Backup

Use diretorio absoluto fora do repositorio. O script usa `pg_dump -Fc`, nome
com data/hora e nunca remove backups:

```powershell
pwsh -File scripts/backup-postgres.ps1 -EnvFile .env.prod -ProjectName monitor-editais-staging -BackupDirectory D:\Backups\MonitorEditais
```

Em Linux com PowerShell, use por exemplo `/srv/backups/monitor-editais`.

## Restauracao controlada

Restaure primeiro em banco de teste existente e explicitamente confirmado:

```powershell
pwsh -File scripts/restore-postgres.ps1 -EnvFile .env.prod -ProjectName monitor-editais-staging -BackupPath D:\Backups\MonitorEditais\monitor_editais_YYYYMMDD_HHMMSS.dump -TargetDatabase monitor_editais_restore_test -ConfirmDatabase monitor_editais_restore_test
```

`-ReplaceExisting` adiciona `--clean --if-exists` e exige cautela. O script
nao cria banco, nao apaga volume e nao remove o backup.

## Rollback

Antes de atualizar:

1. registre o commit/imagem em uso;
2. execute backup;
3. valide o backup em banco controlado;
4. mantenha o scheduler desativado;
5. aplique migration e smoke.

Para rollback da aplicacao, retorne manualmente ao commit/imagem conhecida,
reconstrua e repita health/smoke. Para dados, restaure em banco controlado e
altere a stack somente apos validacao. Nao use `git reset --hard`,
`alembic downgrade` ou remocao de volume como atalho.

## Scheduler

A homologacao inicial deve manter:

```env
CRAWLER_SCHEDULER_ENABLED=false
CRAWLER_INTERVAL_MINUTES=360
UVICORN_WORKERS=1
```

Se habilitado depois, use exatamente uma instancia/processo responsavel.
`max_instances=1` nao coordena replicas diferentes.

## Ambiente Docker descartavel local

Use project name exclusivo, certificado autoassinado criado pela propria tarefa
e portas alternativas. Com mapeamento HTTPS alternativo, acesse diretamente a
porta HTTPS; o redirect HTTP da configuracao publica pressupoe a porta externa 443. Nunca reutilize volumes desconhecidos.

```powershell
docker compose --project-name monitor-editais-remote-staging-test --env-file CAMINHO_ENV_TEMPORARIO -f docker-compose.prod.yml up -d --build --wait
docker compose --project-name monitor-editais-remote-staging-test --env-file CAMINHO_ENV_TEMPORARIO -f docker-compose.prod.yml down
```

Use `down -v` somente se o project name e o volume foram criados e registrados
pela mesma execucao descartavel.
