"""Parse and validate recipe form input."""

from __future__ import annotations

import re
from typing import Any

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
