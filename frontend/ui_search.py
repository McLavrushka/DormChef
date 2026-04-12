"""Ingredient search page (local recipes + TheMealDB section)."""

from __future__ import annotations

import streamlit as st

from api_client import request_api
from recipe_input import parse_comma_separated_items
from ui_mealdb import render_mealdb_meal_ideas_section
from ui_recipes import render_recipe_card


def render_search_page() -> None:
    """Render ingredient-based recipe search."""
    st.header("Search by ingredients")
    st.write(
        "Search **your saved recipes** first, then explore ideas from "
        "TheMealDB by one English main ingredient."
    )

    st.subheader("Your recipes (DormChef)")
    ingredients_input = st.text_input(
        "Ingredients",
        placeholder="egg, tomato, pasta",
        key="dormchef_search_ingredients",
    )
    search_clicked = st.button("Search", type="primary")

    if search_clicked:
        _run_dormchef_ingredient_search(ingredients_input)
    else:
        st.info(
            "Add one or more comma-separated ingredients and click Search."
        )

    st.divider()
    render_mealdb_meal_ideas_section()


def _run_dormchef_ingredient_search(ingredients_input: str) -> None:
    query = ",".join(parse_comma_separated_items(ingredients_input))
    if not query:
        st.error("Please enter at least one ingredient.")
        return
    result = request_api(
        "GET",
        "/recipes/search",
        params={"ingredients": query},
    )
    if not result["ok"]:
        st.error(result["error"])
        return
    if not result["data"]:
        st.warning("No recipes matched your ingredients.")
        return
    recipes = result["data"]
    st.success(f"Found {len(recipes)} matching recipe(s).")
    for recipe in recipes:
        render_recipe_card(recipe)
