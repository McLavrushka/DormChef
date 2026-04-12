"""Recipe list and add-recipe pages."""

from __future__ import annotations

from typing import Any

import streamlit as st

from api_client import request_api
from recipe_input import parse_multiline_items
from recipe_input import strip_leading_step_number
from recipe_input import validate_recipe_payload


def render_add_recipe_page() -> None:
    """Render the recipe creation form."""
    st.header("Add a recipe")
    st.write("Create a new recipe and send it to the DormChef API.")

    with st.form("add_recipe_form", clear_on_submit=True):
        title = st.text_input("Title", placeholder="Creamy Garlic Pasta")
        description = st.text_area(
            "Description",
            placeholder="A quick and filling dinner for a busy evening.",
            height=120,
        )
        ingredients_input = st.text_area(
            "Ingredients",
            placeholder="One ingredient per line",
            height=160,
        )
        steps_input = st.text_area(
            "Steps",
            placeholder="One step per line",
            height=200,
        )
        submitted = st.form_submit_button("Submit")

    if not submitted:
        return

    payload = {
        "title": title.strip(),
        "description": description.strip(),
        "ingredients": parse_multiline_items(ingredients_input),
        "steps": parse_multiline_items(steps_input),
    }

    validation_error = validate_recipe_payload(payload)
    if validation_error:
        st.error(validation_error)
        return

    result = request_api("POST", "/recipes", json=payload)
    if result["ok"]:
        st.success("Recipe created successfully.")
        recipe = result["data"]
        render_recipe_card(recipe, expanded=True)
        return

    st.error(result["error"])


def render_recipe_list_page() -> None:
    """Render a list of all recipes."""
    st.header("All recipes")
    st.write("Browse every recipe currently stored.")

    if st.button("Refresh recipes", use_container_width=False):
        st.rerun()

    result = request_api("GET", "/recipes")
    if not result["ok"]:
        st.error(result["error"])
        return

    recipes = result["data"]
    if not recipes:
        st.info("No recipes found yet.")
        return

    st.caption(f"Loaded {len(recipes)} recipe(s).")
    for recipe in recipes:
        render_recipe_card(recipe)


def render_recipe_card(recipe: dict[str, Any], expanded: bool = False) -> None:
    """Render one recipe as an expandable card."""
    title = recipe.get("title", "Untitled recipe")
    recipe_id = recipe.get("id", "N/A")
    expander_title = f"{title} (ID: {recipe_id})"
    with st.expander(expander_title, expanded=expanded):
        st.write(recipe.get("description", ""))

        ingredients = recipe.get("ingredients") or []
        steps = recipe.get("steps") or []

        st.subheader("Ingredients")
        if ingredients:
            for ingredient in ingredients:
                st.markdown(f"- {ingredient}")
        else:
            st.caption("No ingredients provided.")

        st.subheader("Steps")
        if steps:
            for index, step in enumerate(steps, start=1):
                clean = strip_leading_step_number(step)
                st.markdown(f"{index}. {clean}")
        else:
            st.caption("No steps provided.")
