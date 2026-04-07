"""Endpoint tests for recipe API."""

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
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'api_test.db'}")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _payload(title: str = "Pasta") -> dict[str, object]:
    return {
        "title": title,
        "description": "Simple dorm recipe",
        "ingredients": ["pasta", "salt"],
        "steps": ["Boil water", "Cook pasta"],
    }


@pytest.fixture
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    session_factory = _session_factory(tmp_path)
    app = create_app(init_database=lambda: None)

    def override_get_db() -> Generator[Session, None, None]:
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


def test_create_recipe_endpoint(client: TestClient) -> None:
    response = client.post("/recipes", json=_payload())

    assert response.status_code == 201
    assert response.json()["title"] == "Pasta"


def test_list_recipes_endpoint(client: TestClient) -> None:
    client.post("/recipes", json=_payload("Soup"))
    client.post("/recipes", json=_payload("Rice"))

    response = client.get("/recipes")

    assert response.status_code == 200
    assert [item["title"] for item in response.json()] == ["Soup", "Rice"]


def test_get_recipe_endpoint(client: TestClient) -> None:
    created = client.post("/recipes", json=_payload("Toast"))

    response = client.get(f"/recipes/{created.json()['id']}")

    assert response.status_code == 200
    assert response.json()["steps"] == ["Boil water", "Cook pasta"]


def test_get_recipe_not_found(client: TestClient) -> None:
    response = client.get("/recipes/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


def test_update_recipe_endpoint(client: TestClient) -> None:
    created = client.post("/recipes", json=_payload("Eggs"))
    recipe_id = created.json()["id"]
    response = client.put(
        f"/recipes/{recipe_id}",
        json={"title": "Omelette", "description": "Better recipe"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Omelette"
    assert response.json()["description"] == "Better recipe"
    assert response.json()["ingredients"] == ["pasta", "salt"]


def test_update_recipe_not_found(client: TestClient) -> None:
    response = client.put("/recipes/999", json=_payload())

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


def test_partial_update_title_only(client: TestClient) -> None:
    created = client.post("/recipes", json=_payload("Rice"))
    recipe_id = created.json()["id"]

    response = client.put(
        f"/recipes/{recipe_id}",
        json={"title": "Fried Rice"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Fried Rice"
    assert response.json()["description"] == "Simple dorm recipe"


def test_empty_update_payload_keeps_recipe(client: TestClient) -> None:
    created = client.post("/recipes", json=_payload("Tea"))
    recipe_id = created.json()["id"]

    response = client.put(f"/recipes/{recipe_id}", json={})

    assert response.status_code == 200
    assert response.json()["title"] == "Tea"
    assert response.json()["ingredients"] == ["pasta", "salt"]


def test_delete_recipe_endpoint(client: TestClient) -> None:
    created = client.post("/recipes", json=_payload("Salad"))
    recipe_id = created.json()["id"]

    response = client.delete(f"/recipes/{recipe_id}")
    fetched = client.get(f"/recipes/{recipe_id}")

    assert response.status_code == 204
    assert response.text == ""
    assert fetched.status_code == 404


def test_delete_recipe_not_found(client: TestClient) -> None:
    response = client.delete("/recipes/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Recipe not found"


def test_create_recipe_validation_error(client: TestClient) -> None:
    response = client.post(
        "/recipes",
        json={
            "title": "",
            "description": "bad",
            "ingredients": [],
            "steps": [],
        },
    )

    assert response.status_code == 422


def test_invalid_recipe_id_validation_error(client: TestClient) -> None:
    response = client.get("/recipes/0")

    assert response.status_code == 422
