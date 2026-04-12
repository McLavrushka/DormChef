"""Shared Streamlit chrome (title, sidebar)."""

from __future__ import annotations

import streamlit as st

from config import API_URL


def render_header() -> None:
    """Render app title and sidebar details."""
    st.title("DormChef")
    st.caption(
        "Share simple dorm-friendly recipes and find meals "
        "by ingredients."
    )

    st.sidebar.header("API details")
    st.sidebar.code(API_URL + "/docs")
