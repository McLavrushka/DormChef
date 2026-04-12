"""HTTP client and API error parsing for the Streamlit UI."""

from __future__ import annotations

from typing import Any

import httpx

from config import API_URL
from config import REQUEST_TIMEOUT


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
