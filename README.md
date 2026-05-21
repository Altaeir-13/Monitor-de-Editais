# Monitor de Editais

Plataforma web desenvolvida para centralizar, visualizar e acompanhar editais de instituições públicas. O sistema conta com controle de autenticação, painel administrativo para gestão de fontes e instituições, criação de alertas de usuários, notificações internas e infraestrutura automatizada com Docker.

## Status do Projeto

O **MVP foi concluído e validado** com sucesso em ambiente local-prod. Contudo, atente-se às seguintes condições de contorno nesta etapa:
- **Crawler real por instituição** ainda não está acoplado (a engine base foi validada via mocks/fixtures).
- **SMTP real** para envio automático de e-mails ainda precisa ser configurado.
- **Deploy em nuvem real** (VPS/Cloud) ainda não foi executado.

---

## Funcionalidades Principais

- **Autenticação JWT**: Registro e login seguros com níveis de acesso (Admin/User).
- **Painel Administrativo**: Interface para gerenciar fontes monitoradas e cadastrar instituições.
- **Engine Base de Crawler**: Normalização de editais, prevenção contra duplicados usando fingerprint (SHA256).
- **Visualização de Editais**: Listagem responsiva com paginação e filtros (estado, palavras-chave, tipo e data).
- **Alertas do Usuário**: Parametrização de buscas por palavras-chave, tipo de edital e instituição de interesse.
- **Notificações Internas**: Acoplamento automático que gera avisos internos quando um edital satisfaz os alertas.
- **Dispatcher SMTP**: Rotina de envio de e-mails em lote com acionamento manual administrativo para validação.
- **Tema Claro e Escuro**: Suporte a Dark Mode persistente e com ajustes finos de acessibilidade.
- **Docker local-prod**: Ambiente de build e orquestração completo para testes de produção local.

---

## Stack Tecnológica

### Backend
- **Python 3.11**
- **FastAPI** (Framework API REST)
- **SQLAlchemy** (ORM)
- **Alembic** (Migrações do banco de dados)
- **PostgreSQL** (Banco de dados relacional)
- **PyJWT** (Autenticação baseada em tokens JWT)

### Frontend
- **React 19**
- **Vite** (Build tool e dev server)
- **TypeScript** (Tipagem estática)
- **TailwindCSS 4** (Estilização base e utilitários)
- **Axios** (Requisições HTTP)
- **React Router** (Navegação SPA)
- **TanStack Query** (Gerenciamento de cache e requests)

### Infraestrutura
- **Docker**
- **Docker Compose**
- **Nginx** (Proxy reverso e servidor estático de frontend)

---

## Estrutura do Projeto

Uma visão resumida da árvore de arquivos do repositório:

- [backend](file:///c:/Users/handi/Documents/Working/Development/Editais%20com%20Antigravity/backend): Código-fonte da API Python (FastAPI)
- [frontend](file:///c:/Users/handi/Documents/Working/Development/Editais%20com%20Antigravity/frontend): Interface Web SPA em React
- [docker-compose.yml](file:///c:/Users/handi/Documents/Working/Development/Editais%20com%20Antigravity/docker-compose.yml): Configuração para ambiente de desenvolvimento
- [docker-compose.prod.yml](file:///c:/Users/handi/Documents/Working/Development/Editais%20com%20Antigravity/docker-compose.prod.yml): Configuração para ambiente de produção local
- [docs](file:///c:/Users/handi/Documents/Working/Development/Editais%20com%20Antigravity/docs): Documentação de fechamento e relatórios do projeto
- [README.md](file:///c:/Users/handi/Documents/Working/Development/Editais%20com%20Antigravity/README.md): Guia principal de início rápido

---

## Como Rodar em Desenvolvimento

### 1. Banco de Dados
Inicie o serviço de banco de dados rodando o container PostgreSQL em background:
```bash
docker compose up -d
```

### 2. Backend
Navegue para a pasta do backend, configure o ambiente virtual, instale as dependências e inicie o servidor Uvicorn:
```bash
cd backend
python -m venv venv
# No Windows (PowerShell):
.\venv\Scripts\activate
# No Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
python -m uvicorn main:app --reload
```

### 3. Frontend
Em outro terminal, acesse a pasta do frontend, instale as dependências com npm e execute o dev server:
```bash
cd frontend
npm install
npm run dev
```

---

## Como Rodar local-prod (Docker Compose)

Para rodar a aplicação emulando o ambiente de produção localmente, as variáveis de ambiente `SECRET_KEY` e `POSTGRES_PASSWORD` são obrigatórias.

No terminal (Ex: PowerShell):
```powershell
$env:SECRET_KEY="SUA_CHAVE_SUPER_SEGURA"
$env:POSTGRES_PASSWORD="SENHA_FORTE_DO_BANCO"
docker compose -f docker-compose.prod.yml up -d --build
```
Acesse a aplicação no seu navegador em:
`http://localhost`

> [!WARNING]
> **Observação Importante sobre o Banco de Dados (Persistência)**:
> Se o volume do Postgres (`postgres_prod_data`) já existir de execuções passadas, alterar a variável `POSTGRES_PASSWORD` depois não altera a senha interna do banco de dados automaticamente (o banco aplica o segredo apenas no primeiro boot do volume). Para testar alterações de credenciais em ambiente de testes limpo, pode ser necessário deletar o volume associado executando `docker compose down -v`. Em ambiente de produção real, **nunca** remova volumes sem um backup prévio consolidado.

---

## Variáveis de Ambiente

As configurações de variáveis para produção devem seguir o modelo fornecido no arquivo [.env.prod.example](file:///c:/Users/handi/Documents/Working/Development/Editais%20com%20Antigravity/.env.prod.example).
> [!IMPORTANT]
> Nunca versione ou suba arquivos `.env` com segredos reais para repositórios públicos.

---

## Limitações Conhecidas

- **Spiders Reais**: Os conectores específicos de raspagem para portais como UFPI, IFPI, IFMA etc. ainda não foram implementados.
- **Scheduler Automático**: Rotinas periódicas automatizadas no background não estão habilitadas por padrão.
- **SMTP Real**: O envio de alertas por e-mail ainda carece de parametrização de credenciais ativas reais (está operando via simulações e logs controlados de erros).
- **Deploy**: Inexistência de configuração de DNS, CDN e certificado HTTPS configurados para um servidor de produção externo na nuvem.

---

## Roadmap

- [ ] Desenvolvimento de crawlers/spiders reais com seletores específicos por instituição.
- [ ] Configuração de SMTP real para entrega efetiva de e-mails de notificação.
- [ ] Ativação do scheduler automático (APScheduler) no container de backend.
- [ ] Implementação de suporte a HTTPS (certificados SSL via Let's Encrypt).
- [ ] Configuração de rotina automatizada de backup de banco de dados.
- [ ] Criação de pipeline de CI/CD para deploy contínuo.
- [ ] Deploy definitivo do ambiente Dockerizado em servidor Cloud/VPS.

---

## Licença

Licença: a definir.

---

## Documentação de Fechamento

Para informações técnicas completas sobre cada etapa, modelagem, decisões de arquitetura e validações detalhadas do MVP, consulte:
- [docs/Resumo_Final_MVP.md](file:///c:/Users/handi/Documents/Working/Development/Editais%20com%20Antigravity/docs/Resumo_Final_MVP.md)
