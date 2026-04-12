"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field


class RecipeCreate(BaseModel):
    """Payload for recipe creation."""

    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    ingredients: list[str] = Field(..., min_length=1)
    steps: list[str] = Field(..., min_length=1)


class RecipeUpdate(RecipeCreate):
    """Payload for recipe update."""

    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, min_length=1)
    ingredients: list[str] | None = Field(None, min_length=1)
    steps: list[str] | None = Field(None, min_length=1)


class RecipeResponse(RecipeCreate):
    """Recipe returned by the API."""

    id: int
    model_config = ConfigDict(from_attributes=True)


class MealDbMealSummary(BaseModel):
    """Meal summary from TheMealDB (English, public API)."""

    id: str = Field(..., description="TheMealDB meal id")
    name: str = Field(..., description="Meal title")
    thumbnail: str | None = Field(
        None,
        description="Thumbnail image URL from TheMealDB",
    )


class MealDbRecipeDetail(BaseModel):
    """Full meal from TheMealDB lookup (shown in-app)."""

    id: str
    name: str
    category: str | None = None
    area: str | None = None
    thumbnail: str | None = None
    ingredients: list[str]
    instructions: str
    youtube: str | None = None
