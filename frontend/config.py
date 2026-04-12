"""Shared frontend configuration."""

from __future__ import annotations

import os

API_URL = os.getenv("API_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 10.0
