# DormChef 🍳

A recipe sharing web app for students. Search recipes by ingredients you already have.

## Tech Stack
- **Backend:** FastAPI + SQLite
- **Frontend:** Streamlit
- **Dependency management:** Poetry
- **CI/CD:** GitHub Actions

## Project Structure

```
dormchef/
├── .github/
│   └── workflows/
│       └── ci.yml
├── backend/

├── frontend/
│   ├── __init__.py
│   └── app.py
├── tests/
├── locustfile.py
├── pyproject.toml
└── README.md
```

## Getting Started

```bash
# Install dependencies
poetry install

# Run backend //not completed yet
poetry run uvicorn backend.main:app --reload

# Run frontend (in a separate terminal) //not completed yet
poetry run streamlit run frontend/app.py
```

## Branch Strategy

```
main   ← stable versions only (never push directly)
  ↑
  PR (2 approvals required + CI green)
  ↑
dev    ← main working branch
  ↑
  PR (1 approval required + CI green)
  ↑
feature/your-task  ← your personal branch
```

## Git Workflow

**1. Always start from updated dev:**
```bash
git checkout dev
git pull origin dev
git checkout -b feature/your-task-name
```

**2. Make small, frequent commits while working:**
```bash
git add .
git commit -m "Add POST /recipes endpoint"
git push origin feature/your-task-name
```

**3. When done — open Pull Request into `dev` on GitHub, notify the team in chat.**

**4. Someone else reviews and approves — then you merge.**

## Commit Message Rules

Format: `Verb + what was done`

✅ Good:
```
Add POST /recipes endpoint
Add unit tests for search algorithm
Fix flake8 errors in models.py
Add OpenFoodF
