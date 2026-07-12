# AGENTS.md

## Project

Monitor de Editais aggregates public notices from official institutional sources.
The repository contains a FastAPI backend, SQLAlchemy/Alembic persistence, a
Python crawler and scheduler, plus a React/TypeScript/Vite frontend.

## Stable architecture

- Development may use SQLite; shared staging and production use PostgreSQL.
- The production topology has one public Nginx service serving the built SPA and
  proxying `/api` to FastAPI.
- PostgreSQL and FastAPI have no host port bindings.
- The PostgreSQL volume is persistent and scoped by the Compose project name.
- Alembic runs as the one-shot `migrate` service before the backend starts.
- `CRAWLER_SCHEDULER_ENABLED=false` is the initial remote default.
- If the scheduler is enabled later, exactly one backend process/instance owns it.

## Backend commands

Run from `backend`:

```powershell
venv\Scripts\python.exe -m compileall app tests scripts
venv\Scripts\python.exe tests\test_scheduler.py
venv\Scripts\python.exe tests\test_sqlite_compatibility.py
venv\Scripts\python.exe tests\test_auth.py
venv\Scripts\python.exe tests\test_crawler.py
venv\Scripts\python.exe tests\test_create_admin.py
venv\Scripts\python.exe tests\test_health.py
venv\Scripts\python.exe tests\test_config.py
venv\Scripts\python.exe tests\test_smoke_test.py
venv\Scripts\python.exe tests\test_seed.py
```

Tests that write data must select an isolated temporary SQLite database before
importing application settings. Never run data-writing tests against staging or
production.

## Frontend commands

Run npm only from `frontend`:

```powershell
npm ci
npm run lint
npm run build
npm audit
```

Do not create `package.json`, `package-lock.json`, `node_modules`, or
`dist` at the repository root.

## Docker commands

From the repository root:

```powershell
docker compose --env-file .env.prod.example -f docker-compose.prod.yml config --quiet
docker compose --env-file .env.prod.example -f docker-compose.prod.yml build
```

Use a unique `--project-name` for disposable validation. Never reuse unknown
volumes and never run `down -v` unless the project name and volumes were
created and recorded by the current task.

## Git policy

Before editing, inspect branch, status, history, and remotes. Preserve unrelated
user changes. Never run commit, push, merge, rebase, reset --hard, remote branch
deletion, or destructive cleanup automatically. Never use `git add .`; list
every file in each `git add` command.

## Manual gates

User action is required for commit, push, pull request, merge, remote access,
DNS changes, real certificate issuance, real secrets, global software
installation, destructive database/volume operations, and materially different
business choices.

## Files that must never be versioned

- `.env` files containing real values;
- TLS certificates and private keys;
- database files, dumps, backups, and restore scratch files;
- tokens, passwords, SSH keys, or SMTP credentials;
- virtual environments, `node_modules`, build output, caches, and logs.

## Minimum validation

Before delivery, run applicable backend tests, frontend install/lint/build/audit,
Compose config/build, disposable runtime checks, `git diff --check`,
`git status --short`, and `git diff --stat`. Review every untracked file.
Do not report a validation as passed unless the command was executed.

## Subagents

Use common engineering subagents for independent read-only discovery, testing,
or final review. Assign non-overlapping file ownership before parallel edits.
Do not run concurrent npm installs, migrations, or Compose projects with the
same project name.

## Required final delivery

Report the result and architecture, subagents and findings, every created or
changed file, every validation and failure, remaining operational inputs, and
Git branch/status/diff. Provide manual commit groups with exact messages and
individual `git add <file>` commands, followed by push and pull-request text.
Do not execute those Git writes.
