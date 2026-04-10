"""OpenFoodFacts API integration for ingredient suggestions."""

from __future__ import annotations

import httpx

OPENFOODFACTS_SEARCH_URL = (
    "https://search.openfoodfacts.org/search"
)
USER_AGENT = "DormChef/1.0 (student project)"
DEFAULT_TIMEOUT = 5.0
DEFAULT_PAGE_SIZE = 5


async def fetch_ingredient_suggestions(
    query: str,
    *,
    page_size: int = DEFAULT_PAGE_SIZE,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[str]:
    """Query OpenFoodFacts for product names matching *query*.

    Uses the Search-a-licious API with limited fields to
    reduce payload size.

    Returns a deduplicated list of product names (up to *page_size*).
    """
    params = {
        "q": query,
        "fields": "product_name",
        "page_size": page_size,
    }
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient(
        timeout=timeout, headers=headers,
    ) as client:
        response = await client.get(
            OPENFOODFACTS_SEARCH_URL, params=params,
        )
        response.raise_for_status()

    hits = response.json().get("hits", [])
    seen: set[str] = set()
    suggestions: list[str] = []
    for product in hits:
        name = product.get("product_name", "").strip()
        key = name.lower()
        if name and key not in seen:
            seen.add(key)
            suggestions.append(name)
    return suggestions
