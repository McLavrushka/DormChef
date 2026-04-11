"""Tests for TheMealDB client helpers."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import MagicMock

import pytest

from backend import themealdb_client
from backend.themealdb_client import meal_detail_dict_from_api
from backend.themealdb_client import normalize_main_ingredient


def _run(coro: Any) -> Any:
    return asyncio.run(coro)


def test_http_get_json_builds_url_and_parses_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover real httpx call path without network."""

    class _FakeClient:
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            assert kwargs.get("follow_redirects") is True
            assert kwargs.get("trust_env") is False

        async def __aenter__(self) -> _FakeClient:
            return self

        async def __aexit__(self, *args: Any) -> None:
            return None

        async def get(
            self,
            url: str,
            params: dict[str, str] | None = None,
        ) -> Any:
            base = "https://www.themealdb.com/api/json/v1/1/lookup.php"
            assert url == base
            assert params == {"i": "9"}
            resp = MagicMock()
            resp.raise_for_status = MagicMock()
            resp.json = MagicMock(return_value={"meals": None})
            return resp

    monkeypatch.setattr(themealdb_client.httpx, "AsyncClient", _FakeClient)
    out = _run(themealdb_client._http_get_json("lookup.php", {"i": "9"}))
    assert out == {"meals": None}


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("chicken breast", "chicken_breast"),
        ("  salmon  ", "salmon"),
        ("", ""),
    ],
)
def test_normalize_main_ingredient(raw: str, expected: str) -> None:
    assert normalize_main_ingredient(raw) == expected


def test_meal_detail_dict_from_api() -> None:
    raw = {
        "idMeal": "99",
        "strMeal": "Test Dish",
        "strCategory": "Test",
        "strArea": "Somewhere",
        "strInstructions": "Step one.\r\nStep two.",
        "strIngredient1": "Salt",
        "strMeasure1": "1 tsp",
        "strIngredient2": "Pepper",
        "strMeasure2": "",
        "strIngredient3": "",
    }
    d = meal_detail_dict_from_api(raw)
    assert d["id"] == "99"
    assert d["name"] == "Test Dish"
    assert d["ingredients"] == ["1 tsp Salt", "Pepper"]
    assert "Step one" in d["instructions"]


@pytest.mark.parametrize("meal_id", ["", "  ", "abc", "12a"])
def test_fetch_meal_detail_by_id_invalid_id_returns_none(
    meal_id: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called: list[str] = []

    async def _fake_http(*_a: Any, **_kw: Any) -> dict[str, Any]:
        called.append("no")
        return {}

    monkeypatch.setattr(themealdb_client, "_http_get_json", _fake_http)
    assert _run(themealdb_client.fetch_meal_detail_by_id(meal_id)) is None
    assert called == []


def test_fetch_meal_detail_by_id_no_meals_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_http(*_a: Any, **_kw: Any) -> dict[str, Any]:
        return {"meals": None}

    monkeypatch.setattr(themealdb_client, "_http_get_json", _fake_http)
    assert _run(themealdb_client.fetch_meal_detail_by_id("99")) is None


def test_fetch_meal_detail_by_id_empty_meals_list_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_http(*_a: Any, **_kw: Any) -> dict[str, Any]:
        return {"meals": []}

    monkeypatch.setattr(themealdb_client, "_http_get_json", _fake_http)
    assert _run(themealdb_client.fetch_meal_detail_by_id("1")) is None


def test_fetch_meal_detail_by_id_bad_first_row_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_http(*_a: Any, **_kw: Any) -> dict[str, Any]:
        return {"meals": [{"strMeal": "X"}]}

    monkeypatch.setattr(themealdb_client, "_http_get_json", _fake_http)
    assert _run(themealdb_client.fetch_meal_detail_by_id("1")) is None


def test_fetch_meal_detail_by_id_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "idMeal": "42",
        "strMeal": "Soup",
        "strCategory": None,
        "strArea": None,
        "strInstructions": "Mix.",
        "strIngredient1": "Water",
        "strMeasure1": "1 cup",
    }

    async def _fake_http(path: str, params: dict[str, str], **_kw: Any) -> Any:
        assert path == "lookup.php"
        assert params == {"i": "42"}
        return {"meals": [payload]}

    monkeypatch.setattr(themealdb_client, "_http_get_json", _fake_http)
    out = _run(themealdb_client.fetch_meal_detail_by_id(" 42 "))
    assert out is not None
    assert out["id"] == "42"
    assert out["name"] == "Soup"
    assert "Water" in out["ingredients"][0]


@pytest.mark.parametrize("raw", ["", "   ", "\t"])
def test_fetch_meal_summaries_empty_ingredient_returns_empty(
    raw: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_http(*_a: Any, **_kw: Any) -> dict[str, Any]:
        msg = "HTTP should not be called"
        raise AssertionError(msg)

    monkeypatch.setattr(themealdb_client, "_http_get_json", _fake_http)
    coro = themealdb_client.fetch_meal_summaries_by_main_ingredient(raw)
    assert _run(coro) == []


def test_fetch_meal_summaries_no_meals_key_returns_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_http(*_a: Any, **_kw: Any) -> dict[str, Any]:
        return {}

    monkeypatch.setattr(themealdb_client, "_http_get_json", _fake_http)
    out = _run(themealdb_client.fetch_meal_summaries_by_main_ingredient("egg"))
    assert out == []


def test_fetch_meal_summaries_filters_incomplete_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _fake_http(path: str, params: dict[str, str], **_kw: Any) -> Any:
        assert path == "filter.php"
        assert params == {"i": "chicken_breast"}
        return {
            "meals": [
                {"idMeal": "1", "strMeal": "A", "strMealThumb": "http://x"},
                {"idMeal": "", "strMeal": "B"},
                {"strMeal": "C"},
            ],
        }

    monkeypatch.setattr(themealdb_client, "_http_get_json", _fake_http)
    coro = themealdb_client.fetch_meal_summaries_by_main_ingredient(
        "chicken breast",
    )
    out = _run(coro)
    assert len(out) == 1
    assert out[0] == {
        "id": "1",
        "name": "A",
        "thumbnail": "http://x",
    }
