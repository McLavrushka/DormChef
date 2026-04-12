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
├── backend/           # FastAPI: `main.py`, `schemas.py`, `deps.py`, `routes/`, models, DB, search, TheMealDB client
├── frontend/          # Streamlit UI: `app.py` (entry) + `config`, `api_client`, `recipe_input`, `ui_*`
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

## Quality at a glance (techniques · tools · metrics)

One table tying **what we test**, **which tool enforces it**, **where it lives**, and **numbers we measured** (snapshot: clean tree, no `mutants/`, Python **3.13**; `CI=true` for pytest counts unless noted).

| Technique / goal | Tool(s) | Where | Metric / outcome |
|------------------|---------|-------|------------------|
| **Unit & API tests** | pytest | `tests/test_themealdb_client.py`, `tests/test_search.py` | **29/29** passed  |
| **HTTP + app + DB (TestClient)** | pytest | `tests/test_search.py` — `test_search_endpoint_*` | **3/3** passed |
| **Property-based tests** | Hypothesis, pytest | `tests/test_search.py` — `test_property_*` | **2/2** passed 
| **Line coverage gate** | pytest-cov | `[tool.coverage.run]` omit rules | **96%** TOTAL; gate **≥70%** |
| **E2E (Streamlit UI)** | Selenium, pytest | `tests/test_e2e.py` | CI: **2 skipped**; local: **2 passed** (~**9.7 s**) — API + UI + Chrome |
| **Mutation testing** | mutmut 3 | `[tool.mutmut]`, `backend/search.py` | **35 / 36** killed, **1** survivor |
| **Load / performance** | Locust | `locustfile.py` |**1050** reqs, **0** fails; **P95** average is **26ms** |
| **Style / lint** | flake8 | CI, pre-commit, `[tool.flake8]` | **0** violations |
| **Security (SAST)** | bandit | CI `bandit -r . -lll`, pre-commit | **0 High**, **0 Medium** |
| **Cyclomatic complexity** | radon (report), **`check_max_cc.py`** (gate) | `scripts/check_max_cc.py`, `backend/`, `frontend/` | **≤ 9** per block |
| **Maintainability index** | radon mi | CI (non-blocking) | **66.3** (`radon mi .`); **68.6** (`backend` + `frontend`) |
| **OpenAPI documentation** | Custom check on `app.openapi()` | `.github/workflows/ci.yml` | **PASS** |
| **CI & dependencies** | Poetry, GitHub Actions | `pyproject.toml`, `poetry.lock`, `.github/workflows/ci.yml` | Push/PR to `main`, `dev` |
| **Local git hooks** | pre-commit | `.pre-commit-config.yaml` |  `poetry run pre-commit install` |
| **Containers** | Docker, Docker Compose | `Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` | Demo / deploy stack |







### Commands to reproduce each metric

Run from the **repository root**. If **`mutants/`** exists, run **`rm -rf mutants`** before **flake8**, **bandit**, or **`radon mi .`** so results match CI.

- **Tests (pass / skip):** `CI=true poetry run pytest -q`
- **Unit & API only (exclude Hypothesis property tests):** `CI=true poetry run pytest tests/test_themealdb_client.py tests/test_search.py -k "not property" -q` → **29 passed** (pytest prints the count on the last line).
- **FastAPI `TestClient` HTTP tests only:** `CI=true poetry run pytest tests/test_search.py -k "search_endpoint" -q` → **3 passed**.
- **Property-based (Hypothesis) only:** `CI=true poetry run pytest tests/test_search.py -k "property" -q` → **2 passed** (each test runs many examples; pytest still reports two tests).
- **Pure unit (no `TestClient` endpoint tests):** `CI=true poetry run pytest tests/test_themealdb_client.py tests/test_search.py -k "not property and not search_endpoint" -q` → **26 passed**.
- **Line coverage:** `CI=true poetry run pytest --cov=. --cov-report=term -q` — use the **TOTAL** row (CI uses the same with `--cov-fail-under=70`).
- **CC gate (≤ 9):** `poetry run python scripts/check_max_cc.py`
- **CC report (informational):** `poetry run radon cc backend frontend -s -a`
- **MI per file:** `poetry run radon mi backend frontend -s` or `poetry run radon mi . -s`
- **MI average (backend + frontend):**

```bash
poetry run radon mi backend frontend --json | python3 -c \
  "import json,sys; d=json.load(sys.stdin); s=[v['mi'] for v in d.values()]; print(f'{sum(s)/len(s):.1f}')"
```

- **MI average (whole repo):**

```bash
poetry run radon mi . --json | python3 -c \
  "import json,sys; d=json.load(sys.stdin); s=[v['mi'] for v in d.values()]; print(f'{sum(s)/len(s):.1f}')"
```

- **MI (same as CI — human-readable + average / WARNING):** see the **Radon MI** step in `.github/workflows/ci.yml` (`radon mi . -s` plus the `--json` snippet).
- **flake8:** `poetry run flake8 .`
- **bandit:** `poetry run bandit -r . -lll`
- **OpenAPI (every operation has summary or description):** **Check OpenAPI docs** step in `.github/workflows/ci.yml` (copy the `poetry run python -c "..."` block).
- **Mutation testing:** `poetry run mutmut run`, then `poetry run mutmut results`
- **E2E (Selenium)** — not run in CI; needs **Chrome + ChromeDriver** (matching versions):

  1. Ensure **`CI` is unset** or not `true` (otherwise tests are skipped).
  2. **Terminal 1 — API:**  
     `poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8000`
  3. **Terminal 2 — Streamlit:**  
     `poetry run streamlit run frontend/app.py`  
     (UI at [http://localhost:8501](http://localhost:8501), API URL in sidebar should match the backend.)
  4. **Terminal 3 — tests:**  
     `poetry run pytest tests/test_e2e.py -v`  
     (or full suite without `CI=true`: `poetry run pytest -q` → **55 passed** if both E2E run.)

- **Locust (load / P95)** — API must be up; Locust does not start Streamlit.

  1. **Terminal 1:**     `poetry run uvicorn backend.main:app --host 0.0.0.0 --port 8000`
  2. **Terminal 2** — examples from `locustfile.py` docstring:

```bash
# All tasks (default)
poetry run locust -f locustfile.py --headless \
 -u 50 -r 5 -t 30s --host http://localhost:8000

# Only internal routes (/recipes, /recipes/search)
poetry run locust -f locustfile.py --headless --tags internal \
  -u 50 -r 5 -t 30s --host http://localhost:8000

# Only TheMealDB proxy routes (use lower -u; hits real API)
poetry run locust -f locustfile.py --headless --tags external \
  -u 20 -r 2 -t 30s --host http://localhost:8000
```

  Read **P95** (and other percentiles) from the **headless summary** in the terminal, or open the Locust web UI if you omit `--headless`.

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
