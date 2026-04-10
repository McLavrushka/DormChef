"""Integration tests for the full recipe lifecycle.

Each scenario exercises the real FastAPI app with an in-memory SQLite
database — no mocks, no external services.
"""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from backend.database import create_sqlite_engine
from backend.database import get_db
from backend.main import create_app
from backend.models import Base


def _session_factory(tmp_path: Path) -> sessionmaker:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'int.db'}")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    factory = _session_factory(tmp_path)
    app = create_app(init_database=lambda: None)

    def override() -> Generator[Session, None, None]:
        session = factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override
    with TestClient(app) as c:
        yield c


# ------------------------------------------------------------------
# Scenario 1: create -> appears in list -> fetch by id
# ------------------------------------------------------------------

def test_create_and_find_in_list(client: TestClient) -> None:
    """A newly created recipe must appear in the full listing."""
    payload = {
        "title": "Omelette",
        "description": "Quick breakfast",
        "ingredients": ["egg", "salt", "butter"],
        "steps": ["Beat eggs", "Fry in butter"],
    }
    created = client.post("/recipes", json=payload)
    assert created.status_code == 201
    recipe_id = created.json()["id"]

    listing = client.get("/recipes")
    assert listing.status_code == 200
    ids = [r["id"] for r in listing.json()]
    assert recipe_id in ids

    detail = client.get(f"/recipes/{recipe_id}")
    assert detail.status_code == 200
    assert detail.json()["title"] == "Omelette"


# ------------------------------------------------------------------
# Scenario 2: create -> search by ingredient -> found
# ------------------------------------------------------------------

def test_create_and_search_by_ingredient(client: TestClient) -> None:
    """A recipe is discoverable via ingredient search."""
    client.post("/recipes", json={
        "title": "Tomato Soup",
        "description": "Warm and simple",
        "ingredients": ["tomato", "onion", "salt"],
        "steps": ["Chop", "Boil", "Blend"],
    })
    client.post("/recipes", json={
        "title": "Pancakes",
        "description": "Sweet breakfast",
        "ingredients": ["flour", "milk", "egg"],
        "steps": ["Mix", "Fry"],
    })

    result = client.get(
        "/recipes/search", params={"ingredients": "tomato"},
    )
    assert result.status_code == 200
    titles = [r["title"] for r in result.json()]
    assert "Tomato Soup" in titles
    assert "Pancakes" not in titles


# ------------------------------------------------------------------
# Scenario 3: create -> update -> verify changes persisted
# ------------------------------------------------------------------

def test_create_update_and_verify(client: TestClient) -> None:
    """Updated fields are persisted and returned correctly."""
    created = client.post("/recipes", json={
        "title": "Rice",
        "description": "Plain rice",
        "ingredients": ["rice", "water"],
        "steps": ["Boil water", "Add rice", "Wait"],
    })
    recipe_id = created.json()["id"]

    updated = client.put(
        f"/recipes/{recipe_id}",
        json={"title": "Fried Rice", "ingredients": ["rice", "egg", "soy"]},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "Fried Rice"
    assert updated.json()["ingredients"] == ["rice", "egg", "soy"]
    assert updated.json()["description"] == "Plain rice"

    fetched = client.get(f"/recipes/{recipe_id}")
    assert fetched.json()["title"] == "Fried Rice"


# ------------------------------------------------------------------
# Scenario 4: create -> delete -> gone from list and 404
# ------------------------------------------------------------------

def test_create_delete_and_verify_gone(client: TestClient) -> None:
    """Deleted recipe disappears from listings and returns 404."""
    created = client.post("/recipes", json={
        "title": "Toast",
        "description": "Simple toast",
        "ingredients": ["bread", "butter"],
        "steps": ["Toast bread", "Spread butter"],
    })
    recipe_id = created.json()["id"]

    delete_resp = client.delete(f"/recipes/{recipe_id}")
    assert delete_resp.status_code == 204

    assert client.get(f"/recipes/{recipe_id}").status_code == 404

    listing = client.get("/recipes")
    ids = [r["id"] for r in listing.json()]
    assert recipe_id not in ids


# ------------------------------------------------------------------
# Scenario 5: search with multiple ingredients ranks by match count
# ------------------------------------------------------------------

def test_search_ranks_by_match_count(client: TestClient) -> None:
    """Recipes with more matching ingredients appear first."""
    client.post("/recipes", json={
        "title": "Salad",
        "description": "Fresh salad",
        "ingredients": ["tomato", "lettuce", "onion"],
        "steps": ["Chop", "Mix"],
    })
    client.post("/recipes", json={
        "title": "Pasta",
        "description": "Tomato pasta",
        "ingredients": ["pasta", "tomato", "onion", "garlic"],
        "steps": ["Boil", "Sauce", "Mix"],
    })

    result = client.get(
        "/recipes/search",
        params={"ingredients": "tomato,onion,garlic"},
    )
    titles = [r["title"] for r in result.json()]
    assert titles.index("Pasta") < titles.index("Salad")
