"""Streamlit frontend for the DormChef project."""

from __future__ import annotations

import streamlit as st

from ui_layout import render_header
from ui_recipes import render_add_recipe_page
from ui_recipes import render_recipe_list_page
from ui_search import render_search_page


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


if __name__ == "__main__":
    main()
