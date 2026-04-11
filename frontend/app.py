"""Streamlit frontend for the DormChef project."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
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

    st.sidebar.header("API details")
    st.sidebar.code(API_URL + "/docs")


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
        query = ",".join(parse_comma_separated_items(ingredients_input))
        if not query:
            st.error("Please enter at least one ingredient.")
        else:
            result = request_api(
                "GET",
                "/recipes/search",
                params={"ingredients": query},
            )
            if not result["ok"]:
                st.error(result["error"])
            elif not result["data"]:
                st.warning("No recipes matched your ingredients.")
            else:
                recipes = result["data"]
                st.success(f"Found {len(recipes)} matching recipe(s).")
                for recipe in recipes:
                    render_recipe_card(recipe)
    else:
        st.info(
            "Add one or more comma-separated ingredients and click Search."
        )

    st.divider()
    render_mealdb_meal_ideas_section()


def _mealdb_detail_header(detail: dict[str, Any]) -> None:
    st.caption("Recipe data from TheMealDB (English).")
    st.subheader(detail.get("name", "Recipe"))
    parts = [p for p in (detail.get("category"), detail.get("area")) if p]
    if parts:
        st.caption(" · ".join(parts))


def _mealdb_detail_ingredients_and_steps(detail: dict[str, Any]) -> None:
    st.markdown("**Ingredients**")
    for line in detail.get("ingredients") or []:
        st.markdown(f"- {line}")
    st.markdown("**Instructions**")
    text = (detail.get("instructions") or "").replace("\r\n", "\n\n")
    st.markdown(text)


def _mealdb_detail_youtube(detail: dict[str, Any]) -> None:
    yt = detail.get("youtube")
    if not yt or not str(yt).startswith("http"):
        return
    st.markdown("**Video**")
    st.video(str(yt))


def render_mealdb_detail(detail: dict[str, Any]) -> None:
    """Render full TheMealDB recipe inside the app."""
    _mealdb_detail_header(detail)
    _mealdb_detail_ingredients_and_steps(detail)
    _mealdb_detail_youtube(detail)


@st.dialog("TheMealDB recipe", width="large")
def _mealdb_recipe_dialog(meal_id: str) -> None:
    with st.spinner("Loading recipe…"):
        dr = request_api(
            "GET",
            f"/external/themealdb/meals/{meal_id}",
            timeout=45.0,
        )
    if not dr["ok"]:
        st.error(dr["error"])
        return
    render_mealdb_detail(dr["data"])


def _mealdb_run_search(main_ing: str, finder: bool) -> None:
    if not finder:
        return
    query = main_ing.strip()
    if not query:
        st.warning("Enter a main ingredient.")
        return
    with st.spinner("Loading from TheMealDB…"):
        result = request_api(
            "GET",
            "/external/themealdb/meals",
            params={"ingredient": query},
            timeout=45.0,
        )
    if not result["ok"]:
        st.error(result["error"])
        return
    if not result["data"]:
        st.info("No meals found. Try another English name (e.g. salmon).")
        st.session_state.themealdb_meals = []
        return
    st.session_state.themealdb_meals = result["data"]


def _mealdb_list_result_rows(meals: list[Any]) -> None:
    st.success(f"Found {len(meals)} meal(s).")
    for item in meals:
        mid = str(item.get("id", ""))
        with st.container():
            st.markdown(f"**{item.get('name', 'Meal')}**")
            if st.button("Open recipe", key=f"mdb_detail_btn_{mid}"):
                _mealdb_recipe_dialog(mid)


def render_mealdb_meal_ideas_section() -> None:
    """Show meals from TheMealDB that use a given main ingredient."""
    if "themealdb_meals" not in st.session_state:
        st.session_state.themealdb_meals = None

    st.subheader("Recipe ideas (TheMealDB)")
    st.caption(
        "Public meals filtered by **one main ingredient** in English "
        "(e.g. chicken, rice). Use **Open recipe** for ingredients and steps."
    )
    main_ing = st.text_input(
        "Main ingredient",
        placeholder="chicken",
        key="themealdb_main_ingredient",
    )
    finder = st.button("Find meals", key="themealdb_meal_find")
    _mealdb_run_search(main_ing, finder)

    meals = st.session_state.themealdb_meals
    if not meals:
        return

    _mealdb_list_result_rows(meals)


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


_STEP_NUM_PREFIX = re.compile(r"^\d+[\.\)]\s*")


def strip_leading_step_number(text: str) -> str:
    """Strip a leading '1.' / '2)' prefix so display is not duplicated."""
    s = text.strip()
    return _STEP_NUM_PREFIX.sub("", s, count=1).strip() or s


def parse_multiline_items(raw_value: str) -> list[str]:
    """Convert a multi-line text field into a clean string list."""
    items: list[str] = []
    for line in raw_value.splitlines():
        item = line.strip()
        if not item:
            continue
        item = strip_leading_step_number(item)
        if item:
            items.append(item)
    return items


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
    timeout: float | None = None,
) -> dict[str, Any]:
    """Perform an API request and normalize success/error responses."""
    effective_timeout = REQUEST_TIMEOUT if timeout is None else timeout
    try:
        with httpx.Client(
            base_url=API_URL,
            timeout=effective_timeout,
        ) as client:
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
        return extract_error_detail_from_mapping(data)

    if isinstance(data, list):
        return join_error_details(data)

    if isinstance(data, str):
        return data

    return ""


def extract_error_detail_from_mapping(data: dict[str, Any]) -> str:
    """Extract a readable detail message from a mapping payload."""
    detail = data.get("detail")
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return join_error_details(detail)
    return ""


def join_error_details(items: list[Any]) -> str:
    """Join nested error messages into one readable string."""
    parts = [extract_error_detail(item) for item in items]
    return "; ".join(part for part in parts if part)


if __name__ == "__main__":
    main()
