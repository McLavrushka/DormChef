"""Streamlit frontend for the DormChef project."""

from __future__ import annotations

from typing import Any

import httpx
import streamlit as st

API_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 10.0


def main() -> None:
    """Render the DormChef frontend."""
    st.set_page_config(
        page_title="DormChef",
        page_icon=":fork_and_knife:",
        layout="wide",
    )
    render_header()

    page = st.sidebar.radio(
        "Choose a page",
        options=(
            "Add recipe",
            "Browse recipes",
            "Search by ingredients",
        ),
    )

    if page == "Add recipe":
        render_add_recipe_page()
    elif page == "Browse recipes":
        render_recipe_list_page()
    else:
        render_search_page()


def render_header() -> None:
    """Render app title and sidebar details."""
    st.title("DormChef")
    st.caption(
        "Share simple dorm-friendly recipes and find meals "
        "by ingredients."
    )

    st.sidebar.header("API")
    st.sidebar.code(API_URL)


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
    st.write("Browse every recipe currently stored in the backend.")

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


def render_search_page() -> None:
    """Render ingredient-based recipe search."""
    st.header("Search by ingredients")
    st.write(
        "Enter the ingredients you already have and "
        "find matching recipes."
    )

    ingredients_input = st.text_input(
        "Ingredients",
        placeholder="egg, tomato, pasta",
    )
    search_clicked = st.button("Search", type="primary")

    if not search_clicked:
        st.info(
            "Add one or more comma-separated ingredients "
            "to start searching."
        )
        return

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

    recipes = result["data"]
    if not recipes:
        st.warning("No recipes matched your ingredients.")
        return

    st.success(f"Found {len(recipes)} matching recipe(s).")
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
                st.markdown(f"{index}. {step}")
        else:
            st.caption("No steps provided.")


def parse_multiline_items(raw_value: str) -> list[str]:
    """Convert a multi-line text field into a clean string list."""
    return [item.strip() for item in raw_value.splitlines() if item.strip()]


def parse_comma_separated_items(raw_value: str) -> list[str]:
    """Convert comma-separated input into a clean string list."""
    seen: set[str] = set()
    items: list[str] = []
    for part in raw_value.split(","):
        token = part.strip()
        token_key = token.lower()
        if token and token_key not in seen:
            seen.add(token_key)
            items.append(token)
    return items


def validate_recipe_payload(payload: dict[str, Any]) -> str | None:
    """Validate recipe fields before sending them to the backend."""
    if not payload["title"]:
        return "Title is required."
    if not payload["description"]:
        return "Description is required."
    if not payload["ingredients"]:
        return "Please add at least one ingredient."
    if not payload["steps"]:
        return "Please add at least one preparation step."
    return None


def request_api(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform an API request and normalize success/error responses."""
    try:
        with httpx.Client(base_url=API_URL, timeout=REQUEST_TIMEOUT) as client:
            response = client.request(method, path, params=params, json=json)
            response.raise_for_status()
    except httpx.HTTPStatusError as error:
        return {"ok": False, "error": build_http_error_message(error.response)}
    except httpx.RequestError:
        return {
            "ok": False,
            "error": (
                "Could not connect to the backend. "
                "Make sure the API is running on http://localhost:8000."
            ),
        }

    return {"ok": True, "data": response.json()}


def build_http_error_message(response: httpx.Response) -> str:
    """Build a user-friendly error message from an API response."""
    message = f"Request failed with status {response.status_code}."
    try:
        data = response.json()
    except ValueError:
        return message

    detail = extract_error_detail(data)
    if detail:
        return f"{message} {detail}"
    return message


def extract_error_detail(data: Any) -> str:
    """Extract a readable detail message from API error payloads."""
    if isinstance(data, dict):
        detail = data.get("detail")
        if isinstance(detail, str):
            return detail
        if isinstance(detail, list):
            parts = [extract_error_detail(item) for item in detail]
            return "; ".join(part for part in parts if part)
        return ""

    if isinstance(data, list):
        parts = [extract_error_detail(item) for item in data]
        return "; ".join(part for part in parts if part)

    if isinstance(data, str):
        return data

    return ""


if __name__ == "__main__":
    main()
