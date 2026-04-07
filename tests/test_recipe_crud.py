"""Tests for recipe CRUD operations."""

from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from backend.database import create_recipe
from backend.database import delete_recipe
from backend.database import get_recipe
from backend.database import list_recipes
from backend.database import update_recipe
from backend.models import Base


def _session_factory(tmp_path: Path) -> sessionmaker:
    database_path = tmp_path / "test_recipes.db"
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(bind=engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _recipe_payload() -> dict[str, object]:
    return {
        "title": "Egg Toast",
        "description": "Quick dorm breakfast",
        "ingredients": ["egg", "bread", "salt"],
        "steps": ["Beat egg", "Toast bread", "Combine"],
    }


@pytest.fixture
def session(tmp_path: Path) -> Session:
    session_factory = _session_factory(tmp_path)
    with session_factory() as db_session:
        yield db_session


def test_create_recipe(session: Session) -> None:
    created = create_recipe(session, **_recipe_payload())

    assert created.id is not None
    assert created.title == "Egg Toast"


def test_get_recipe(session: Session) -> None:
    created = create_recipe(session, **_recipe_payload())

    fetched = get_recipe(session, created.id)

    assert fetched is not None
    assert fetched.ingredients == ["egg", "bread", "salt"]


def test_update_recipe(session: Session) -> None:
    created = create_recipe(session, **_recipe_payload())

    updated = update_recipe(
        session,
        created.id,
        description="Quick breakfast in 10 minutes",
        ingredients=["egg", "bread", "salt", "pepper"],
    )

    assert updated is not None
    assert updated.description == "Quick breakfast in 10 minutes"
    assert "pepper" in updated.ingredients


def test_list_recipes(session: Session) -> None:
    create_recipe(session, **_recipe_payload())

    all_recipes = list_recipes(session)

    assert len(all_recipes) == 1


def test_delete_recipe(session: Session) -> None:
    created = create_recipe(session, **_recipe_payload())

    assert delete_recipe(session, created.id) is True
    assert get_recipe(session, created.id) is None
