# Resumo Final do MVP — Monitor de Editais

## 1. Objetivo do Sistema
Plataforma projetada para consolidar a coleta de editais de fontes institucionais públicas. O sistema permite centralizar oportunidades (concursos, vagas, licitações, processos seletivos) e preparar o disparo de notificações baseadas em interesses do usuário, como palavras-chave, tipo de edital e, quando configurado, instituição.

## 2. Stack Usada
- **Backend**: Python 3.11, FastAPI, SQLAlchemy (ORM), Alembic (Migrations), APScheduler, PyJWT, Passlib, psycopg2.
- **Frontend**: React 19, Vite, TypeScript, TailwindCSS 4 (base/utilities) + CSS Vanilla HSL, Axios, React Router, TanStack Query (React Query), Lucide React.
- **Infraestrutura/Deploy**: Docker, Docker Compose, Nginx, PostgreSQL 15.

## 3. Etapas Concluídas
- Etapa 1 — Infraestrutura e Setup Inicial
- Etapa 2 — Banco de Dados e Modelagem
- Etapa 3 — Autenticação e API de Usuários
- Etapa 4 — Módulos Administrativos Backend
- Etapa 5 — Engenharia do Crawler (Engine base de Scraping)
- Etapa 6 — API de Editais e Visualização Backend
- Etapa 7 — Alertas e Notificações Backend
- Etapa 8 — Frontend Administrativo e Telas de Usuário (8A a 8D)
- Etapa 9 — Envio de E-mails / SMTP
- Etapa 10 — Refinamento UI/UX (Acessibilidade + Dark Mode Persistente)
- Etapa 11 — Preparação para Deploy (Preparação para deploy com Docker validada em ambiente local-prod)

## 4. Funcionalidades Implementadas

### Implementado e validado no MVP
- **Autenticação e Sessão**: Sistema de Registro e Login JWT, rotas protegidas por cargo (Admin/User).
- **Painel Administrativo**: Gestão de Fontes Monitoradas e Instituições sob usuários com perfil admin.
- **Engenharia do Crawler**: O MVP possui uma engine base de crawler validada com fixture/mock (Scraping). Implementa normalização lexical e hashes de prevenção contra editais duplicados (Fingerprint SHA256).
- **Motor de Alertas e Match**: CRUD de palavras-chave vigiadas; lógica de vinculação que detecta novos editais e gera notificações internas aguardando envio.
- **Interface de Visualização de Editais autenticada**: Listagem rica contando com paginação e filtros (Datas, Estado, Palavras-chave, Tipo). A API de leitura de editais existe no backend como pública, mas no frontend o acesso foi protegido por autenticação integrada ao layout com sidebar.
- **Dispatcher SMTP**: Dispatcher de e-mails em lote implementado e com envio manual/admin validado por mock/teste. O dispatcher processa notificações com status `pending` alterando-as para `sent` ou registrando erros em `failed`. Um endpoint administrativo permite disparar manualmente este fluxo. O SMTP real ainda precisa ser configurado.
- **Arquitetura Resiliente Dockerizada**: Servidor Nginx em proxy reverso resolvendo rotas do SPA e requests `/api` para o backend (elimina problemas clássicos de CORS).

### Preparado, mas dependente de configuração
- **Disparo Automático de E-mails**: O scheduler automático não está habilitado nesta versão. A rotina automática depende da configuração SMTP real definitiva pelo time de infra.

### Futuro
- **Ações Ativas do Crawler**: A arquitetura está pronta para receber spiders reais por instituição. Crawlers reais para UFPI, IFPI, IFMA etc. ainda são próximos passos.
- **Integração Automática Completa**: Fechamento do pipeline com o Crawler e Dispatcher executando via rotinas periódicas completas no background.
- **Integração OAuth**: Autenticação externalizada (ex. login via Conta Google).

## 5. Como Rodar em Desenvolvimento
1. Levante o banco base via Docker: `docker compose up -d`
2. **Backend**: Acesse `/backend`, ative um `virtualenv`, instale o `requirements.txt`, configure o arquivo `.env` e suba o Uvicorn via:
   `python -m uvicorn main:app --reload`
3. **Frontend**: Acesse `/frontend`, instale os pacotes (`npm install`) e inicie o dev server do Vite:
   `npm run dev`

## 6. Como Rodar local-prod com Docker Compose
O repositório possui um arranjo pronto para deploy baseado no `docker-compose.prod.yml`, o qual foi validado com sucesso em ambiente local-prod.

> [!NOTE]
> **Status do Deploy**: O ambiente local-prod foi validado com sucesso no host de desenvolvimento. Contudo, ainda não houve deploy em nuvem real. Configurações de HTTPS/SSL, apontamento de domínio definitivo e estratégias de backup são próximos passos essenciais para colocar o sistema no ar em produção.

1. Configure as variáveis mandatórias no sistema operacional (Ex. PowerShell):
   ```powershell
   $env:SECRET_KEY="SUA_CHAVE_SUPER_SEGURA"
   $env:POSTGRES_PASSWORD="SENHA_FORTIFICADA_DO_BANCO"
   ```
2. Processe a orquestração gerando o build isolado:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```
3. Acesse via `http://localhost` (Frontend SPA gerido por Nginx interceptando chamadas para `/api`).

> [!WARNING]
> **Atenção sobre o Banco (Persistência)**: Se o volume do Postgres (`postgres_prod_data`) já existir e a variável `POSTGRES_PASSWORD` for alterada depois, o banco não troca a senha automaticamente. A senha inicial só é aplicada na primeira criação do volume. Para testes locais limpos, pode ser necessário remover o volume com `docker compose down -v`. Em produção real, nunca remover volume sem backup.

## 7. Variáveis de Ambiente Principais
Baseie-se no artefato `.env.prod.example` da raiz. As diretivas de obrigatoriedade do Compose são `SECRET_KEY` e `POSTGRES_PASSWORD`.

## 8. Funcionalidades que Podem Entrar no Futuro
- Desenvolvimento contínuo de conectores Crawler de diferentes DOMs.
- Transbordo de alertas via Webhooks (Telegram/WhatsApp API).
- Gestão massiva de relatórios analíticos de envio de disparo no admin.

## 9. Limitações Conhecidas
- Em ambientes sem SMTP configurado de fato, as notificações tentam enviar e falham com graciosidade (status `failed`) retendo log do erro sem quebrar a API.
- As integrações dependem estritamente do mapeamento manual dos seletores HTML (Spiders) das fontes externas para que o mock dê lugar à produção.

## 10. Próximas Recomendações
1. **Scraping Real**: Criar spiders reais (seletores web/JSON) mapeados para instituições específicas.
2. **Testes de E-mail**: Configurar SMTP real ou mock seguro (ex: Mailtrap) e efetuar testagem com usuários base.
3. **Ativação da Automação**: Configurar e habilitar o scheduler no código apenas depois de validar a coleta dos crawlers reais e os envios manuais em produção.
4. **Resiliência de Dados**: Criar backup robusto do PostgreSQL antes de acoplar o banco a um deploy real vivo em Cloud.
5. **HTTPS**: Configurar HTTPS para tráfego em rede, gerando um certificado confiável no Nginx ou provedor/Gateway.
6. **Automação de Deploy**: Preparar pipeline de CI/CD (ex. GitHub Actions, GitLab CI) para validar e aplicar releases contínuos livre de atritos.
