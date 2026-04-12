"""Shared FastAPI dependency and path annotations."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from fastapi import Path
from sqlalchemy.orm import Session

from backend.database import get_db

DbSession = Annotated[Session, Depends(get_db)]
RecipeId = Annotated[
    int,
    Path(..., ge=1, description="Recipe identifier"),
]
MealDbExternalId = Annotated[
    str,
    Path(
        ...,
        pattern=r"^[0-9]+$",
        description="TheMealDB numeric meal id",
    ),
]
