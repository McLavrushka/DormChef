# DormChef Backend

FastAPI backend for storing and reading recipes in SQLite.

## Features

- Create recipe: `POST /recipes`
- List recipes: `GET /recipes`
- Get one recipe: `GET /recipes/{recipe_id}`
- Update recipe: `PUT /recipes/{recipe_id}`
- Delete recipe: `DELETE /recipes/{recipe_id}`
- OpenAPI docs: `GET /docs`

## Recipe schema

```json
{
  "title": "Pasta",
  "description": "Simple dorm recipe",
  "ingredients": ["pasta", "salt"],
  "steps": ["Boil water", "Cook pasta"]
}
```

## Run locally

```bash
poetry install --with dev
poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Docs:

```text
http://localhost:8000/docs
```

## Environment

- `DATABASE_URL`
  - Local default: `sqlite:///./dormchef.db`
  - Docker default: `sqlite:////app/data/dormchef.db`

## Endpoint details

### `POST /recipes`

Create a new recipe.

Response:

- `201 Created`
- Returns created recipe with `id`

### `GET /recipes`

Return all recipes in creation order.

Response:

- `200 OK`
- Returns array of recipes

### `GET /recipes/{recipe_id}`

Return one recipe by id.

Response:

- `200 OK`
- `404 Not Found` if recipe does not exist

### `PUT /recipes/{recipe_id}`

Update only provided fields by id.

Response:

- `200 OK`
- `404 Not Found` if recipe does not exist

### `DELETE /recipes/{recipe_id}`

Delete recipe by id.

Response:

- `204 No Content`
- `404 Not Found` if recipe does not exist

## Run tests

```bash
poetry run pytest
poetry run pytest --cov=backend --cov-report=term-missing
```

## Docker

Build and start:

```bash
docker compose up --build
```

Docs:

```text
http://localhost:8000/docs
```

If port `8000` is busy:

```bash
APP_PORT=8001 docker compose up --build
```
