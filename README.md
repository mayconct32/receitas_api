# Sistema de Compartilhamento de Receitas

Documentação geral da aplicação completa (frontend + backend + infraestrutura).
Para a documentação detalhada da API (endpoints, exemplos curl, etc.), consulte [server/README.md](server/README.md).

## Visão geral

A aplicação é uma plataforma de compartilhamento de receitas composta por dois módulos principais:

- **`server/`** — API REST em Python (FastAPI) responsável por autenticação de chefs, gerenciamento de receitas, upload de imagens, cache, paginação e rate limit.
- **`client/`** — Interface web em Python (Streamlit) que consome a API e oferece telas de listagem, cadastro, edição e exclusão de receitas, além de autenticação e gerenciamento de perfil do chef.

O fluxo principal é: um chef se cadastra, faz login e recebe um token JWT. Com esse token, ele pode criar, editar e excluir **apenas as próprias** receitas. Usuários não autenticados podem navegar e visualizar receitas e chefs publicamente.

## Estrutura do repositório

```
receitas_api/
├── server/                  # Backend (API REST)
│   ├── src/
│   │   ├── main.py                  # Ponto de entrada do FastAPI (app, middlewares, exception handlers)
│   │   ├── database.py              # Conexões MySQL (pool), MongoDB e Redis
│   │   ├── dependencies.py          # Injeção de dependências (auth, repos, serviços)
│   │   ├── exceptions.py            # Exceções de domínio (DomainException)
│   │   ├── rate_limiter.py          # Rate limiting com SlowAPI (por IP)
│   │   ├── utils.py                 # Utilitários
│   │   ├── chef_table.sql           # Script de criação da tabela `chef` (MySQL)
│   │   ├── api/v1/routers/
│   │   │   ├── chefs.py             # Rotas de chefs (/v1/chefs)
│   │   │   └── recipes.py           # Rotas de receitas (/v1/recipes)
│   │   ├── models/
│   │   │   ├── chef.py              # Modelos Pydantic de chef (Chef, UpdateChef, ResponseChef)
│   │   │   ├── recipe.py            # Modelos Pydantic de receita (Recipe, ResponseRecipe, ...)
│   │   │   └── auth.py              # Modelo de token JWT
│   │   ├── services/
│   │   │   ├── chef_service.py      # Regras de negócio de chef
│   │   │   ├── recipe_service.py    # Regras de negócio de receita
│   │   │   ├── auth_service.py      # Autenticação JWT e hashing (pwdlib/argon2)
│   │   │   ├── cache_service.py     # Leitura/escrita/invalidação de cache Redis
│   │   │   └── storage_service.py   # Upload/exclusão de imagens (S3 via LocalStack)
│   │   ├── repositories/
│   │   │   ├── chef_repository.py   # Acesso ao MySQL (chefs)
│   │   │   ├── recipe_repository.py # Acesso ao MongoDB (receitas)
│   │   │   └── redis_repository.py  # Acesso ao Redis (cache)
│   │   └── interfaces/
│   │       ├── repository.py        # Contratos dos repositórios
│   │       ├── connection_db.py     # Contratos de conexão com bancos
│   │       └── storage.py           # Contrato do serviço de storage
│   ├── tests/                       # Testes de integração com FastAPI TestClient
│   ├── Dockerfile
│   ├── docker-compose.yml           # Orquestra: app + MySQL + MongoDB + Redis + LocalStack
│   ├── pyproject.toml               # Dependências do servidor (Poetry)
│   ├── .env.example                 # Modelo de variáveis de ambiente
│   └── README.md                    # Documentação detalhada da API
│
└── client/                  # Frontend (Streamlit)
    ├── src/
    │   ├── main.py                  # Ponto de entrada: navegação e página inicial
    │   ├── api/
    │   │   ├── chefs.py             # Cliente HTTP das rotas /v1/chefs
    │   │   └── recipes.py           # Cliente HTTP das rotas /v1/recipes
    │   ├── helpers/
    │   │   └── ui.py                # Helpers de UI (renderização, parsing, sessão)
    │   └── pages/
    │       ├── auth/                # Login, cadastro, perfil, minhas receitas, excluir conta
    │       ├── chefs/               # Listagem e detalhe de chefs
    │       └── recipes/             # Receitas públicas, detalhe, criar, atualizar, excluir
    ├── pyproject.toml               # Dependências do cliente (Poetry): streamlit, streamlit-redirect
    └── README.md
```

## Arquitetura da solução

```
┌────────────────┐      HTTP (requests)      ┌─────────────────────┐
│  client/       │  ───────────────────────► │  server/ (FastAPI)  │
│  Streamlit UI  │   http://127.0.0.1:8000   │  prefixo /v1        │
└────────────────┘                           └─────────┬───────────┘
                                                       │
              ┌────────────┬────────────┬──────────────┼──────────────┐
              ▼            ▼            ▼              ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐
        │  MySQL   │ │ MongoDB  │ │  Redis   │ │ S3 (LocalStack) │
        │ (chefs)  │ │(receitas)│ │ (cache)  │ │ (imagens)       │
        └──────────┘ └──────────┘ └──────────┘ └─────────────────┘
```

### Papéis de cada armazenamento

- **MySQL 8.4** — dados estruturados de chefs e credenciais de autenticação (tabela `chef` com `chef_id`, `chef_name` único, `email` único, `password_hash`, timestamps). Inicializada via `src/chef_table.sql`.
- **MongoDB 7.0** — documentos das receitas (nome, descrição, tempo de preparo, instruções, ingredientes, `image_url`, `chef_id`, timestamps).
- **Redis 7.2** — cache de consultas frequentes (listagens e detalhes de chefs e receitas), com invalidação após criação/atualização/exclusão.
- **S3 compatível (LocalStack)** — imagens das receitas; a URL pública do objeto é persistida no campo `image_url` da receita.

## Backend (server/)

### Tecnologias

- Python 3.13, FastAPI, Uvicorn, Pydantic, PyJWT, pwdlib[argon2], SlowAPI, mysql-connector-python, pymongo, redis[hiredis], boto3, python-dotenv.
- Gerenciamento de dependências com Poetry; lint/formatação com Ruff (`line-length = 78`).

### Camadas

O backend segue uma arquitetura em camadas com injeção de dependências:

1. **Routers** (`api/v1/routers/`) — definem os endpoints sob o prefixo `/v1`, com `response_model` e limites de requisição por IP via SlowAPI.
2. **Services** (`services/`) — concentram as regras de negócio (autenticação, ownership, cache, upload de imagem).
3. **Repositories** (`repositories/`) — acesso a dados isolado por tecnologia (MySQL, MongoDB, Redis), seguindo os contratos em `interfaces/`.
4. **Models** (`models/`) — esquemas Pydantic de entrada e saída.
5. **Exceptions** — `DomainException` convertida em resposta JSON com `status_code` e `detail` por um handler global.

Comportamentos transversais:

- **Middleware HTTP** que adiciona o header `X-Process-Time` com o tempo de processamento de cada requisição.
- **CORS** aberto (`allow_origins=['*']`).
- **Rate limit** por IP com SlowAPI (ex.: `GET /` com `30/minute`; `POST /v1/chefs/auth` com `20/minute`; escrita em chefs/receitas com `15/minute`; leitura com `30/minute`).
- **Autenticação** JWT (HS256), expiração configurável via `ACCESS_TOKEN_EXPIRE_MINUTES` (padrão 60 min).
- **Paginação** das listagens com `offset` e `limit`.
- **Cache** Redis para consultas, invalidado em operações de escrita.
- **Imagens** enviadas como `multipart/form-data` (campo `recipe_data` com JSON + campo `image` opcional) nos endpoints de criação/atualização de receita; na exclusão da receita, a imagem associada é removida do storage.

## Frontend (client/)

### Tecnologias

- Python 3.13+, Streamlit 1.64+, streamlit-redirect.
- Comunicação com a API via biblioteca `requests`, apontando para `http://127.0.0.1:8000/v1`.

### Funcionamento

O ponto de entrada (`src/main.py`) registra as páginas com `st.Page` e monta a navegação com `st.navigation`, **diferente conforme o estado de autenticação**:

- **Deslogado**: acesso apenas às receitas públicas, listagem/detalhe de chefs e páginas de **Cadastrar** e **Entrar**.
- **Logado** (quando `token` está em `st.session_state`): liberadas as páginas **Minhas receitas**, **Nova receita**, **Atualizar receita**, **Excluir receita**, **Meu perfil**, **Editar perfil** e **Excluir conta**.

Detalhes relevantes:

- O token JWT é armazenado em `st.session_state.token` após o login e enviado no header `Authorization: Bearer <token>` nas chamadas autenticadas.
- O módulo `api/` encapsula todas as chamadas HTTP e trata erros retornando dicionários com `error`/`detail`, que os helpers de UI convertem em mensagens amigáveis.
- `helpers/ui.py` possui utilidades como `parse_instructions` (formato `1. descrição` por linha), `parse_ingredients` (formato `nome: quantidade`, padrão `a gosto`), `render_recipe` (exibe também a imagem quando `image_url` existe) e `require_token` (bloqueia páginas que exigem autenticação).
- Erros de formulário exibem mensagens vindas do `detail`/`error` retornado pela API.

## Como executar a aplicação completa

### Pré-requisitos

- Docker e Docker Compose (para o backend + infraestrutura) **ou** os serviços MySQL, MongoDB, Redis e LocalStack rodando localmente.
- Python 3.13+ e Poetry (para o cliente, e para o backend se for rodá-lo fora do Docker).

### 1. Subir o backend e a infraestrutura

```bash
cd server
cp .env.example .env   # ajuste se necessário
docker compose up -d
```

A API ficará disponível em `http://localhost:8000` (documentação interativa Swagger em `http://localhost:8000/docs`).

Alternativa sem Docker (requer os bancos e o LocalStack rodando separadamente):

```bash
cd server
poetry install
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Subir o frontend

```bash
cd client
poetry install
poetry run streamlit run src/main.py
```

O Streamlit abre a interface em `http://localhost:8501`, que consome a API em `http://127.0.0.1:8000`.

## Configuração (variáveis de ambiente do servidor)

Base: `server/.env.example`.

| Variável | Descrição |
|---|---|
| `MYSQL_HOST`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_ROOT_PASSWORD` | Conexão e credenciais do MySQL |
| `MySQL_PORT`, `MYSQL_POOL_SIZE`, `MYSQL_POOL_NAME` | Porta e configuração do pool de conexões |
| `MONGO_HOST`, `PORT_MONGO`, `MONGO_INITDB_ROOT_USERNAME`, `MONGO_INITDB_ROOT_PASSWORD`, `MONGO_INITDB_DATABASE` | Conexão e credenciais do MongoDB |
| `MONGO_MIN_POOL_SIZE`, `MONGO_MAX_POOL_SIZE` | Pool de conexões do MongoDB |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_MAX_CONNECTIONS` | Conexão do Redis |
| `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | Configuração do JWT |
| `PORT` | Porta exposta da API (padrão 8000) |
| `AWS_S3_BUCKET`, `AWS_S3_ENDPOINT_URL`, `AWS_S3_PUBLIC_ENDPOINT_URL`, `AWS_DEFAULT_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` | Storage de imagens (S3 via LocalStack) |

## Testes e qualidade

### Backend

- Suíte de **testes de integração** com `FastAPI TestClient` cobrindo rotas de chefs e receitas (autenticação, autorização, validações, ownership, imagens, paginação).
- No CI (GitHub Actions, `.github/workflows/integration-tests.yml`), os testes de integração sobem **Testcontainers** (MySQL, MongoDB e Redis reais) com o marcador `integration`:

```bash
cd server
poetry run pytest -q                    # suíte completa
poetry run pytest -v -m integration     # apenas testes de integração
poetry run pytest --cov=src --cov-report=html -q   # cobertura
```

- Lint e formatação:

```bash
cd server
poetry run ruff check .
poetry run ruff format .
```

## Resumo do funcionamento end-to-end

1. O chef se cadastra pela tela **Cadastrar** (ou `POST /v1/chefs/`) — os dados vão para o MySQL com senha hasheada (argon2).
2. Faz login pela tela **Entrar** (ou `POST /v1/chefs/auth`) e recebe um token JWT, guardado na sessão do Streamlit.
3. Cria uma receita com nome, descrição, tempo de preparo, ingredientes, instruções e uma imagem opcional. A imagem vai para o bucket S3 (LocalStack), e a receita (com `image_url`) vai para o MongoDB.
4. As listagens e detalhes de chefs/receitas são servidos com cache em Redis e paginação.
5. Apenas o chef dono pode atualizar ou excluir suas receitas e o próprio perfil.
