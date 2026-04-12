"""TheMealDB proxy routes."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter
from fastapi import HTTPException
from fastapi import Query
from fastapi import status

from backend.deps import MealDbExternalId
from backend.schemas import MealDbMealSummary
from backend.schemas import MealDbRecipeDetail
from backend.themealdb_client import fetch_meal_detail_by_id
from backend.themealdb_client import fetch_meal_summaries_by_main_ingredient

router = APIRouter(tags=["external"])


@router.get(
    "/external/themealdb/meals",
    response_model=list[MealDbMealSummary],
    summary="Meals by main ingredient (TheMealDB)",
    description=(
        "Filter public meals by main ingredient in English "
        "(e.g. chicken, salmon). Multi-word values use underscores "
        "in TheMealDB (chicken breast → chicken_breast)."
    ),
)
async def themealdb_meals_endpoint(
    ingredient: Annotated[
        str,
        Query(
            ...,
            min_length=1,
            description="Main ingredient name",
            examples=["chicken"],
        ),
    ],
) -> list[MealDbMealSummary]:
    try:
        rows = await fetch_meal_summaries_by_main_ingredient(ingredient)
        return [MealDbMealSummary(**row) for row in rows]
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="TheMealDB API is unavailable",
        )


@router.get(
    "/external/themealdb/meals/{meal_id}",
    response_model=MealDbRecipeDetail,
    summary="Meal detail by id (TheMealDB)",
    description=(
        "Full recipe text and ingredients from TheMealDB lookup.php "
        "for display inside DormChef."
    ),
)
async def themealdb_meal_detail_endpoint(
    meal_id: MealDbExternalId,
) -> MealDbRecipeDetail:
    try:
        row = await fetch_meal_detail_by_id(meal_id)
        if row is None or not row.get("name"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meal not found",
            )
        return MealDbRecipeDetail(**row)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="TheMealDB API is unavailable",
        )
