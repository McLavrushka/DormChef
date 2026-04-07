from __future__ import annotations

from collections.abc import Generator
from collections.abc import Iterable

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from backend.models import Base
from backend.models import Recipe

# SQLite URL for local app runtime.
DEFAULT_DATABASE_URL = "sqlite:///./dormchef.db"
# Shared engine used by app and tests.
engine = create_engine(
    DEFAULT_DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
# Session factory for endpoint-level transactions.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    # Creates tables if they do not exist.
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    # FastAPI dependency: yields one session per request.
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
    # Stores lists as JSON in SQLite.
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
    # Stable ordering helps deterministic API responses/tests.
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
    # Partial update: only non-null values are applied.
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
