"""Recipe CRUD and ingredient search routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import Response
from fastapi import status

from backend.database import create_recipe
from backend.database import delete_recipe
from backend.database import get_recipe
from backend.database import list_recipes
from backend.database import update_recipe
from backend.deps import DbSession
from backend.deps import RecipeId
from backend.schemas import RecipeCreate
from backend.schemas import RecipeResponse
from backend.schemas import RecipeUpdate
from backend.search import filter_recipes_by_ingredients
from backend.search import parse_ingredient_query

router = APIRouter(tags=["recipes"])


@router.post(
    "/recipes",
    response_model=RecipeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create recipe",
    description=(
        "Create a new recipe with title, description, "
        "ingredients, and steps."
    ),
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


@router.get(
    "/recipes",
    response_model=list[RecipeResponse],
    summary="List recipes",
    description="Return all stored recipes ordered by identifier.",
)
def list_recipes_endpoint(db: DbSession) -> list[RecipeResponse]:
    recipes = list_recipes(db)
    return [RecipeResponse.model_validate(recipe) for recipe in recipes]


@router.get(
    "/recipes/search",
    response_model=list[RecipeResponse],
    summary="Search recipes by ingredients",
    description=(
        "Return recipes that contain at least one of the given pantry "
        "ingredients. Ingredients are comma-separated (e.g. tomato,egg). "
        "Matching is case-insensitive. Better overlaps are listed first."
    ),
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


@router.get(
    "/recipes/{recipe_id}",
    response_model=RecipeResponse,
    summary="Get recipe",
    description="Return one recipe by identifier.",
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


@router.put(
    "/recipes/{recipe_id}",
    response_model=RecipeResponse,
    summary="Update recipe",
    description="Update one or more recipe fields by identifier.",
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


@router.delete(
    "/recipes/{recipe_id}",
    response_model=None,
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
    summary="Delete recipe",
    description="Delete one recipe by identifier.",
)
def delete_recipe_endpoint(recipe_id: RecipeId, db: DbSession) -> Response:
    deleted = delete_recipe(db, recipe_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipe not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
