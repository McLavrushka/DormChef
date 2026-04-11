"""TheMealDB public API (English meals by main ingredient)."""

from __future__ import annotations

from typing import Any

import httpx

MEALDB_BASE = "https://www.themealdb.com/api/json/v1/1"
USER_AGENT = "DormChef/1.0 (student project)"
DEFAULT_TIMEOUT = 10.0


async def _http_get_json(
    path: str,
    params: dict[str, str],
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> Any:
    url = f"{MEALDB_BASE}/{path}"
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(
        timeout=timeout,
        headers=headers,
        follow_redirects=True,
        trust_env=False,
    ) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def normalize_main_ingredient(value: str) -> str:
    """Use underscores for TheMealDB main-ingredient filter values."""
    return value.strip().replace(" ", "_")


def _ingredient_lines_from_meal(raw: dict[str, Any]) -> list[str]:
    """Pair strIngredientN with strMeasureN into readable lines."""
    lines: list[str] = []
    for i in range(1, 21):
        ing = raw.get(f"strIngredient{i}")
        meas = raw.get(f"strMeasure{i}")
        ing_s = str(ing).strip() if ing not in (None, "") else ""
        meas_s = str(meas).strip() if meas not in (None, "") else ""
        if not ing_s:
            continue
        lines.append(
            f"{meas_s} {ing_s}".strip() if meas_s else ing_s,
        )
    return lines


def meal_detail_dict_from_api(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize TheMealDB lookup.php meal object for JSON response."""
    return {
        "id": str(raw.get("idMeal", "")),
        "name": str(raw.get("strMeal", "")),
        "category": raw.get("strCategory"),
        "area": raw.get("strArea"),
        "thumbnail": raw.get("strMealThumb"),
        "ingredients": _ingredient_lines_from_meal(raw),
        "instructions": (raw.get("strInstructions") or "").strip(),
        "youtube": raw.get("strYoutube"),
    }


async def fetch_meal_detail_by_id(meal_id: str) -> dict[str, Any] | None:
    """Return one meal from lookup.php, or None if not found."""
    mid = meal_id.strip()
    if not mid.isdigit():
        return None
    data = await _http_get_json("lookup.php", {"i": mid})
    meals = data.get("meals")
    if not meals or not isinstance(meals, list):
        return None
    first = meals[0]
    if not isinstance(first, dict) or not first.get("idMeal"):
        return None
    return meal_detail_dict_from_api(first)


async def fetch_meal_summaries_by_main_ingredient(
    ingredient: str,
) -> list[dict[str, Any]]:
    """Meal id, name, and thumbnail for this main ingredient."""
    key = normalize_main_ingredient(ingredient)
    if not key:
        return []
    data = await _http_get_json("filter.php", {"i": key})
    raw = data.get("meals") or []
    if not raw:
        return []
    return [
        {
            "id": m["idMeal"],
            "name": m["strMeal"],
            "thumbnail": m.get("strMealThumb"),
        }
        for m in raw
        if isinstance(m, dict) and m.get("idMeal") and m.get("strMeal")
    ]
