from __future__ import annotations

from collections.abc import Generator
from collections.abc import Iterable
from os import getenv
from pathlib import Path

from sqlalchemy import create_engine as sa_create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from backend.models import Base
from backend.models import Recipe

DEFAULT_DATABASE_URL = "sqlite:///./dormchef.db"


def get_database_url() -> str:
    return getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def create_sqlite_engine(database_url: str | None = None):
    url = database_url or get_database_url()
    _prepare_sqlite_path(url)
    return sa_create_engine(
        url,
        connect_args={"check_same_thread": False},
        future=True,
    )


def _prepare_sqlite_path(database_url: str) -> None:
    if database_url == "sqlite:///:memory:":
        return
    database_path = Path(database_url.removeprefix("sqlite:///"))
    if database_path.parent != Path():
        database_path.parent.mkdir(parents=True, exist_ok=True)


engine = create_sqlite_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_recipe(
    session: Session,
    title: str,
    description: str,
    ingredients: Iterable[str],
    steps: Iterable[str],
) -> Recipe:
    recipe = Recipe(
        title=title,
        description=description,
        ingredients=list(ingredients),
        steps=list(steps),
    )
    session.add(recipe)
    session.commit()
    session.refresh(recipe)
    return recipe


def list_recipes(session: Session) -> list[Recipe]:
    return session.query(Recipe).order_by(Recipe.id.asc()).all()


def get_recipe(session: Session, recipe_id: int) -> Recipe | None:
    return session.get(Recipe, recipe_id)


def update_recipe(
    session: Session,
    recipe_id: int,
    *,
    title: str | None = None,
    description: str | None = None,
    ingredients: Iterable[str] | None = None,
    steps: Iterable[str] | None = None,
) -> Recipe | None:
    recipe = get_recipe(session, recipe_id)
    if recipe is None:
        return None
    if title is not None:
        recipe.title = title
    if description is not None:
        recipe.description = description
    if ingredients is not None:
        recipe.ingredients = list(ingredients)
    if steps is not None:
        recipe.steps = list(steps)
    session.commit()
    session.refresh(recipe)
    return recipe


def delete_recipe(session: Session, recipe_id: int) -> bool:
    recipe = get_recipe(session, recipe_id)
    if recipe is None:
        return False
    session.delete(recipe)
    session.commit()
    return True
