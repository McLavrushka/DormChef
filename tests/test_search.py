"""Tests for ingredient search logic and API."""

from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from hypothesis import assume
from hypothesis import given
from hypothesis import strategies as st
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from backend.database import create_sqlite_engine
from backend.database import get_db
from backend.main import create_app
from backend.models import Base
from backend.models import Recipe
from backend.search import count_query_hits
from backend.search import filter_recipes_by_ingredients
from backend.search import normalize_ingredient
from backend.search import parse_ingredient_query
from backend.search import recipe_ingredient_set


def _recipe(
    rid: int,
    title: str,
    ingredients: list[str],
) -> Recipe:
    return Recipe(
        id=rid,
        title=title,
        description="d",
        ingredients=ingredients,
        steps=["step"],
    )


def test_normalize_ingredient_trims_and_lowercases() -> None:
    assert normalize_ingredient("  Tomato  ") == "tomato"


def test_parse_ingredient_query_splits_and_dedupes() -> None:
    assert parse_ingredient_query("Egg, tomato , egg") == ["egg", "tomato"]


def test_parse_ingredient_query_empty_after_trim_is_empty() -> None:
    assert parse_ingredient_query(" , , ") == []


def test_recipe_ingredient_set_normalizes() -> None:
    r = _recipe(1, "x", ["Salt", " salt "])
    assert recipe_ingredient_set(r) == frozenset({"salt"})


def test_filter_recipes_requires_at_least_one_overlap() -> None:
    a = _recipe(1, "A", ["pasta"])
    b = _recipe(2, "B", ["tomato"])
    out = filter_recipes_by_ingredients([a, b], ["tomato"])
    assert [x.id for x in out] == [2]


def test_filter_recipes_orders_by_match_count() -> None:
    light = _recipe(1, "Light", ["egg"])
    heavy = _recipe(2, "Heavy", ["egg", "tomato", "salt"])
    out = filter_recipes_by_ingredients(
        [light, heavy],
        ["egg", "tomato", "salt"],
    )
    assert [r.id for r in out] == [2, 1]


def test_filter_recipes_tiebreaks_by_recipe_id() -> None:
    """Same match count: ascending id (stable secondary key)."""
    hi = _recipe(10, "Hi", ["egg"])
    lo = _recipe(5, "Lo", ["egg"])
    out = filter_recipes_by_ingredients([hi, lo], ["egg"])
    assert [r.id for r in out] == [5, 10]


def test_count_query_hits() -> None:
    r = _recipe(1, "x", ["a", "b", "c"])
    assert count_query_hits(r, ["a", "z"]) == 1
    assert count_query_hits(r, ["a", "b"]) == 2


_WORD = st.sampled_from(["salt", "egg", "tomato", "pasta", "milk", "rice"])


@given(st.lists(_WORD, min_size=1, max_size=6))
def test_property_recipe_with_shared_ingredient_is_returned(
    words: list[str],
) -> None:
    tokens = parse_ingredient_query(",".join(words))
    assume(len(tokens) >= 1)
    recipe = _recipe(1, "r", [words[0]])
    out = filter_recipes_by_ingredients([recipe], tokens)
    assert out == [recipe]


@given(_WORD, _WORD)
def test_property_richer_recipe_ranks_first(a: str, b: str) -> None:
    assume(normalize_ingredient(a) != normalize_ingredient(b))
    r_thin = _recipe(1, "thin", [a])
    r_rich = _recipe(2, "rich", [a, b])
    tokens = parse_ingredient_query(f"{a},{b}")
    assume(len(tokens) >= 2)
    out = filter_recipes_by_ingredients([r_thin, r_rich], tokens)
    assert out[0].id == 2


def _session_factory(tmp_path: Path) -> sessionmaker:
    engine = create_sqlite_engine(f"sqlite:///{tmp_path / 'search_api.db'}")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


def _post_recipe(
    client: TestClient,
    title: str,
    ingredients: list[str],
) -> None:
    client.post(
        "/recipes",
        json={
            "title": title,
            "description": "d",
            "ingredients": ingredients,
            "steps": ["s"],
        },
    )


def test_search_endpoint_returns_matches(client: TestClient) -> None:
    _post_recipe(client, "Omelette", ["egg", "milk"])
    _post_recipe(client, "Salad", ["lettuce"])

    response = client.get(
        "/recipes/search",
        params={"ingredients": "egg,tomato"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Omelette"


def test_search_endpoint_orders_by_overlap(client: TestClient) -> None:
    _post_recipe(client, "One", ["salt"])
    _post_recipe(client, "Two", ["salt", "pepper"])

    response = client.get(
        "/recipes/search",
        params={"ingredients": "salt,pepper"},
    )

    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert titles == ["Two", "One"]


def test_search_endpoint_422_when_no_usable_tokens(client: TestClient) -> None:
    response = client.get("/recipes/search", params={"ingredients": ",,"})

    assert response.status_code == 422
