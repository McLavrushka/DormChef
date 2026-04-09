"""Ingredient-based recipe search."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeVar

from backend.models import Recipe

TRecipe = TypeVar("TRecipe", bound=Recipe)


def normalize_ingredient(name: str) -> str:
    """Return a comparable token (trimmed, lowercased)."""
    return name.strip().lower()


def parse_ingredient_query(raw: str) -> list[str]:
    """
    Split a comma-separated ingredient string into normalized tokens.

    Empty segments are dropped. Duplicates are removed (first occurrence wins).
    """
    if not raw.strip():
        return []
    parts = raw.split(",")
    seen: set[str] = set()
    out: list[str] = []
    for part in parts:
        token = normalize_ingredient(part)
        if token and token not in seen:
            seen.add(token)
            out.append(token)
    return out


def recipe_ingredient_set(recipe: Recipe) -> frozenset[str]:
    """Normalized ingredient names for one recipe."""
    return frozenset(normalize_ingredient(x) for x in recipe.ingredients)


def count_query_hits(recipe: Recipe, query_tokens: Sequence[str]) -> int:
    """How many query tokens appear in this recipe's ingredients."""
    available = recipe_ingredient_set(recipe)
    return sum(1 for token in query_tokens if token in available)


def filter_recipes_by_ingredients(
    recipes: Sequence[TRecipe],
    query_tokens: Sequence[str],
) -> list[TRecipe]:
    """
    Return recipes that use at least one of the query ingredients.

    Results are ordered by descending match count, then by recipe id for
    stable ordering.
    """
    if not query_tokens:
        return []

    scored: list[tuple[int, int, TRecipe]] = []
    for recipe in recipes:
        hits = count_query_hits(recipe, query_tokens)
        if hits > 0:
            scored.append((-hits, recipe.id, recipe))

    scored.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in scored]
