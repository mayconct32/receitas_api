# Sistema de Compartilhamento de Receitas

## Descrição

Este projeto é uma API REST em Python para compartilhar receitas entre chefs e usuários autenticados. A aplicação centraliza o cadastro de perfis, autenticação por JWT, criação e gerenciamento de receitas, além de controles de autorização, paginação, cache e rate limit.

A ideia principal é permitir que um chef cadastre seu perfil, faça login com segurança e gerencie suas receitas de forma isolada, sem que outros chefs possam alterar ou remover conteúdo que não lhes pertença.

## Tecnologias utilizadas

- Python 3.13
- FastAPI
- Uvicorn
- Pydantic
- MySQL 8.4
- MongoDB 7.0
- Redis 7.2
- Docker / Docker Compose
- Poetry
- PyJWT
- SlowAPI
- python-dotenv
- pwdlib[argon2]
- mysql-connector-python
- pymongo
- redis[hiredis]
- Ruff

## Como funciona na prática

Exemplo de autenticação:

```bash
curl -X POST http://localhost:8000/v1/chefs/auth \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=chef@email.com&password=senha123"
```

Resposta esperada:

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

## Instalação

### Opção 1: com Docker

```bash
docker compose up 
```

### Opção 2: localmente

```bash
poetry install
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## Quick Start / Uso básico

### 1. Criar um chef

```bash
curl -X POST http://localhost:8000/v1/chefs/ \
  -H "Content-Type: application/json" \
  -d '{
    "chef_name": "Ana",
    "email": "ana@email.com",
    "password": "senha123"
  }'
```

### 2. Fazer login

```bash
curl -X POST http://localhost:8000/v1/chefs/auth \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=ana@email.com&password=senha123"
```

### 3. Consultar perfil autenticado

```bash
curl -X GET http://localhost:8000/v1/chefs/me \
  -H "Authorization: Bearer <TOKEN>"
```

### 4. Criar uma receita

```bash
curl -X POST http://localhost:8000/v1/recipes/ \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "recipe_name": "Pão caseiro",
    "description": "Receita simples",
    "prep_time": "00:45:00",
    "instructions": [
      {"step_number": 1, "description": "Misture os ingredientes"}
    ],
    "ingredients": [
      {"ingredient_name": "farinha", "quantity": "500g"}
    ]
  }'
```

## Endpoints principais

### Chef

- `POST /v1/chefs/` - cadastra um chef
- `POST /v1/chefs/auth` - autentica um chef e retorna um token JWT
- `GET /v1/chefs/` - lista chefs com paginação (`offset` e `limit`)
- `GET /v1/chefs/me` - retorna o perfil do chef autenticado
- `GET /v1/chefs/{chef_id}` - busca chef por ID
- `PUT /v1/chefs/{chef_id}` - atualiza dados do chef autenticado
- `DELETE /v1/chefs/{chef_id}` - remove o chef autenticado

### Receita

- `POST /v1/recipes/` - cria uma receita para o chef autenticado
- `GET /v1/recipes/` - lista receitas com paginação
- `GET /v1/recipes/my_recipes` - lista as receitas do chef autenticado
- `GET /v1/recipes/{recipe_id}` - busca uma receita por ID
- `PUT /v1/recipes/{recipe_id}` - atualiza uma receita do chef autenticado
- `DELETE /v1/recipes/{recipe_id}` - remove uma receita do chef autenticado

## Documentação interativa

A documentação Swagger da API fica disponível em `http://localhost:8000/docs` quando a aplicação está em execução.

![Swagger da API - chefs](docs/images/swagger_chefs.png)

![Swagger da API - receitas](docs/images/swagger_recipes.png)

## Arquitetura e comportamento da aplicação

### Versionamento da API

A API está versionada por URL com o prefixo `/v1`, o que permite evoluções futuras sem quebrar clientes existentes.

### Autenticação e autorização

- A autenticação usa JWT.
- O login é realizado em `POST /v1/chefs/auth`.
- O token é enviado no header `Authorization: Bearer <TOKEN>`.
- Rotas sensíveis exigem o chef autenticado.
- A autorização é validada no backend para garantir que um chef só possa alterar ou excluir seus próprios dados e receitas.

### Banco de dados

- MySQL: usado para dados estruturados de chef e autenticação.
- MongoDB: usado para armazenar receitas em documentos.
- Redis: usado como cache em memória para consultas frequentes e invalidação após alterações.

### Cache

A aplicação usa Redis para armazenar respostas de consultas como:

- listagem de chefs
- busca por chef
- listagem de receitas
- receitas do chef autenticado
- detalhes de uma receita

Ao criar, atualizar ou excluir dados, o sistema limpa entries relacionadas em Redis para evitar retorno de dados obsoletos.

### Paginação

As listagens principais usam parâmetros `offset` e `limit`, por exemplo:

```bash
GET /v1/chefs/?offset=0&limit=10
GET /v1/recipes/?offset=0&limit=10
```

Isso reduz a carga de dados e melhora o desempenho das consultas.

### Rate limit

A aplicação utiliza SlowAPI para limitar requisições por IP. Esse mecanismo protege endpoints contra abuso e excesso de chamadas em curto período.

Exemplos observados no código:

- `/` com limite de `6/minute`
- endpoints de chefs e receitas com limites de `3/minute` ou `5/minute`

### Docker

O projeto utiliza Docker Compose para orquestrar os serviços principais da aplicação:

- API Python/FastAPI
- MySQL
- MongoDB
- Redis

## Configuração / variáveis de ambiente

Use o arquivo [.env.example](.env.example) como base e copie para `.env` antes de iniciar a aplicação:

```bash
cp .env.example .env
```

Depois, ajuste os valores conforme o seu ambiente local ou o Docker.

As variáveis principais são:

```env
MYSQL_HOST=mysql
MYSQL_DATABASE=recipes_db
MYSQL_USER=recipes_app
MYSQL_PASSWORD=my_strong_password
MYSQL_ROOT_PASSWORD=my_strong_password
MYSQL_POOL_SIZE=5
MYSQL_POOL_NAME=my_pool

MONGO_HOST=mongo
PORT_MONGO=27017
MONGO_INITDB_ROOT_USERNAME=roott
MONGO_INITDB_ROOT_PASSWORD=my_strong_password
MONGO_INITDB_DATABASE=recipes
MONGO_MIN_POOL_SIZE=5
MONGO_MAX_POOL_SIZE=20

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_MAX_CONNECTIONS=20

ACCESS_TOKEN_EXPIRE_MINUTES=60
SECRET_KEY=my_secret_key
ALGORITHM=HS256
PORT=8000
```