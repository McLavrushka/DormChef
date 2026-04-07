"""SQLAlchemy models for DormChef backend."""

from __future__ import annotations

from typing import Any

from sqlalchemy import JSON
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""


class Recipe(Base):
    """Recipe entity stored in SQLite."""

    __tablename__ = "recipes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    ingredients: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    steps: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    def to_dict(self) -> dict[str, Any]:
        """Return API-friendly representation of recipe."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "ingredients": self.ingredients,
            "steps": self.steps,
        }
