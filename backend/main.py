"""FastAPI application for recipe management."""

from __future__ import annotations

from collections.abc import Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database import init_db
from backend.routes import recipes
from backend.routes import themealdb


def create_app(init_database: Callable[[], None] = init_db) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        init_database()
        yield

    api = FastAPI(
        title="DormChef API",
        description="API for creating, viewing, and updating recipes.",
        version="1.0.0",
        lifespan=lifespan,
    )
    api.include_router(recipes.router)
    api.include_router(themealdb.router)
    return api


app = create_app()
