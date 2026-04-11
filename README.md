# DormChef

A web app for sharing simple recipes among students.
 You can add recipes, browse the catalog, and find dishes based on ingredients you already have (“what’s in my fridge?”). Built for a software quality course (SQR), with emphasis on automated CI quality gates and a broad set of testing techniques.

## Features

- **Recipes:** create, read, list, update, and delete via REST API and the Streamlit UI.
- **Ingredient-based search:** match **your** stored recipes to a pantry list (comma-separated ingredients).
- **TheMealDB:** browse public English meals by **one main ingredient** (`GET /external/themealdb/meals`) and open **full text in a dialog** (`GET /external/themealdb/meals/{meal_id}`).
- **API docs:** auto-generated OpenAPI/Swagger from FastAPI (`/docs`).

## Tech stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.11–3.13|
| Dependencies | Poetry |
| Backend | FastAPI, Uvicorn, SQLAlchemy, SQLite |
| Frontend | Streamlit |
| Containers | Docker, Docker Compose |
| CI | GitHub Actions |

## Quick start (Docker Compose)

Recommended for demos and grading: API and frontend start together; SQLite data is stored in a named volume.

```bash
docker compose up --build
```

After startup:

- **API:** [http://localhost:8000](http://localhost:8000) (interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs))
- **Streamlit UI:** [http://localhost:8501](http://localhost:8501)

Override ports with environment variables:

```bash
APP_PORT=8000 FRONTEND_PORT=8501 docker compose up --build
```

Inside the Compose network the frontend calls the API at `http://api:8000` (see `docker-compose.yml`).

## Local run (without Docker)

Install Python (3.11–3.13) and [Poetry](https://python-poetry.org/).

```bash
poetry install
```

**Terminal 1 — backend:**

```bash
poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — frontend** (by default the app expects the API at `http://localhost:8000`):

```bash
poetry run streamlit run frontend/app.py
```

Open the URL printed by the CLI (usually [http://localhost:8501](http://localhost:8501)).

The sidebar shows the **API URL** Streamlit uses (`API_URL`, default `http://localhost:8000`).

## Repository layout

```
├── backend/           # FastAPI app, models, DB, search, TheMealDB client
├── frontend/          # Streamlit UI
├── tests/             # Automated tests (pytest); sole test root (see `tool.pytest.ini_options`)
├── scripts/           # Helpers (e.g. cyclomatic complexity threshold)
├── .github/workflows/ # CI pipeline
├── docker-compose.yml
├── Dockerfile         # API image
├── frontend/Dockerfile
├── locustfile.py      # load testing (local)
├── pyproject.toml     # Poetry
└── mutants/           # gitignored
```

## Testing techniques

| Technique | Where | Notes |
|-----------|-------|-------|
| **Unit tests** | `tests/test_recipes.py`, `tests/test_search.py`, `tests/test_recipe_crud.py`, `tests/test_themealdb_client.py` | Logic, API, TheMealDB client (with HTTP mocked) |
| **Integration tests** | `tests/test_integration.py` | Full recipe lifecycle via `TestClient` and the real app stack |
| **Property-based** | `tests/test_search.py` (Hypothesis) | Normalization and ingredient-query parsing on generated inputs |
| **E2E (UI)** | `tests/test_e2e.py` (Selenium) | Run manually with backend + Streamlit up and Chrome/Chromedriver; skipped in CI |
| **Coverage** | `pytest-cov`, **≥70%** gate in CI | `locustfile.py`, E2E, and frontend code omitted from the report|
| **Mutation testing** | **mutmut 3.x** (dev dependency, pinned in Poetry) | for backend |
| **Load testing** | `locustfile.py` | Run locally against a running internal/external API |

## Static analysis and CI quality gates

GitHub Actions runs on `main` and `dev` (including pull requests):

- **flake8** — style and errors; gate expects a clean run.
- **bandit** — common security issues in Python code.
- **Cyclomatic complexity** — numeric radon threshold: each block **at most 9** (strictly below 10), enforced by `scripts/check_max_cc.py`.
- **Radon MI** — maintainability index; CI prints the average and warns if below target (non-blocking).
- **pytest** — full suite with `--cov-fail-under=70`.
- **OpenAPI** — every HTTP operation must have `summary` or `description` in the schema.

For local commits, **pre-commit** (`.pre-commit-config.yaml`) can run flake8, bandit, and the same CC check.

## External API (TheMealDB)

The app uses the free **[TheMealDB](https://www.themealdb.com/api.php)** JSON API (`v1/1`): **`filter.php?i=…`** for meals by main ingredient, **`lookup.php?i={id}`** for full recipe text. If TheMealDB is unreachable, the backend returns HTTP **502** on those routes; unknown meal id returns **404**.
