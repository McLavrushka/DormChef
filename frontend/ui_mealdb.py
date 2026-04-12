"""TheMealDB browse / detail UI."""

from __future__ import annotations

from typing import Any

import streamlit as st

from api_client import request_api


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
