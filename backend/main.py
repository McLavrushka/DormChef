"""FastAPI application for recipe management."""

from __future__ import annotations

from contextlib import asynccontextmanager
from collections.abc import Callable
from typing import Annotated

from fastapi import Depends
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Path
from fastapi import Query
from fastapi import Response
from fastapi import status
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from sqlalchemy.orm import Session

from backend.database import create_recipe
from backend.database import delete_recipe
from backend.database import get_db
from backend.database import get_recipe
from backend.database import init_db
from backend.database import list_recipes
from backend.database import update_recipe
from backend.external_api import fetch_ingredient_suggestions
from backend.search import filter_recipes_by_ingredients
from backend.search import parse_ingredient_query


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


DbSession = Annotated[Session, Depends(get_db)]
RecipeId = Annotated[
    int,
    Path(..., ge=1, description="Recipe identifier"),
]


def create_app(init_database: Callable[[], None] = init_db) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        init_database()
        yield

    api = FastAPI(
        title="DormChef API",
        description="API for creating, viewing, and updating recipes.",
        version="1.0.0",
        lifespan=lifespan,
    )

    @api.get(
        "/ingredients/suggest",
        response_model=list[str],
        summary="Suggest ingredients",
        description=(
            "Return ingredient suggestions from OpenFoodFacts "
            "matching the query string. Rate-limited to 10 req/min "
            "upstream — use on button press, not per keystroke."
        ),
        tags=["ingredients"],
    )
    async def suggest_ingredients_endpoint(
        q: Annotated[
            str,
            Query(
                ...,
                min_length=1,
                description="Ingredient search query",
                examples=["tomato"],
            ),
        ],
    ) -> list[str]:
        try:
            return await fetch_ingredient_suggestions(q)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="OpenFoodFacts API is unavailable",
            )

    @api.post(
        "/recipes",
        response_model=RecipeResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create recipe",
        description=(
            "Create a new recipe with title, description, "
            "ingredients, and steps."
        ),
        tags=["recipes"],
    )
    def create_recipe_endpoint(
        payload: RecipeCreate,
        db: DbSession,
    ) -> RecipeResponse:
        recipe = create_recipe(
            db,
            title=payload.title,
            description=payload.description,
            ingredients=payload.ingredients,
            steps=payload.steps,
        )
        return RecipeResponse.model_validate(recipe)

    @api.get(
        "/recipes",
        response_model=list[RecipeResponse],
        summary="List recipes",
        description="Return all stored recipes ordered by identifier.",
        tags=["recipes"],
    )
    def list_recipes_endpoint(db: DbSession) -> list[RecipeResponse]:
        recipes = list_recipes(db)
        return [RecipeResponse.model_validate(recipe) for recipe in recipes]

    @api.get(
        "/recipes/search",
        response_model=list[RecipeResponse],
        summary="Search recipes by ingredients",
        description=(
            "Return recipes that contain at least one of the given pantry "
            "ingredients. Ingredients are comma-separated (e.g. tomato,egg). "
            "Matching is case-insensitive. Better overlaps are listed first."
        ),
        tags=["recipes"],
    )
    def search_recipes_endpoint(
        db: DbSession,
        ingredients: Annotated[
            str,
            Query(
                ...,
                min_length=1,
                description="Comma-separated ingredients from your pantry",
                examples=["tomato,egg"],
            ),
        ],
    ) -> list[RecipeResponse]:
        tokens = parse_ingredient_query(ingredients)
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Provide at least one ingredient after trimming",
            )
        recipes = list_recipes(db)
        matched = filter_recipes_by_ingredients(recipes, tokens)
        return [RecipeResponse.model_validate(r) for r in matched]

    @api.get(
        "/recipes/{recipe_id}",
        response_model=RecipeResponse,
        summary="Get recipe",
        description="Return one recipe by identifier.",
        tags=["recipes"],
    )
    def get_recipe_endpoint(
        recipe_id: RecipeId,
        db: DbSession,
    ) -> RecipeResponse:
        recipe = get_recipe(db, recipe_id)
        if recipe is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )
        return RecipeResponse.model_validate(recipe)

    @api.put(
        "/recipes/{recipe_id}",
        response_model=RecipeResponse,
        summary="Update recipe",
        description="Update one or more recipe fields by identifier.",
        tags=["recipes"],
    )
    def update_recipe_endpoint(
        recipe_id: RecipeId,
        payload: RecipeUpdate,
        db: DbSession,
    ) -> RecipeResponse:
        recipe = update_recipe(
            db,
            recipe_id,
            title=payload.title,
            description=payload.description,
            ingredients=payload.ingredients,
            steps=payload.steps,
        )
        if recipe is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )
        return RecipeResponse.model_validate(recipe)

    @api.delete(
        "/recipes/{recipe_id}",
        response_model=None,
        status_code=status.HTTP_204_NO_CONTENT,
        response_class=Response,
        summary="Delete recipe",
        description="Delete one recipe by identifier.",
        tags=["recipes"],
    )
    def delete_recipe_endpoint(recipe_id: RecipeId, db: DbSession) -> Response:
        deleted = delete_recipe(db, recipe_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Recipe not found",
            )
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return api


app = create_app()
