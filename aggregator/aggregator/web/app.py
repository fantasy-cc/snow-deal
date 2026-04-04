"""FastAPI application factory."""

from __future__ import annotations

import logging
import os
import secrets
from contextlib import asynccontextmanager
from pathlib import Path

from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import aggregator.auth as auth
from aggregator.auth import auth_middleware
from aggregator.db import init_db
from aggregator.auth_db import init_auth_db
from aggregator.web.routes import router
from aggregator.web.invite_routes import invite_router
from aggregator.web.admin_routes import admin_router
from aggregator.web.event_routes import event_router

log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"

templates = Jinja2Templates(directory=str(TEMPLATE_DIR))


@asynccontextmanager
async def lifespan(app: FastAPI):
    auth.ensure_auth_config()
    await init_db()
    await init_auth_db()
    # Auto-generate admin key for local development if not set
    if not auth.get_admin_key():
        admin_key = secrets.token_urlsafe(16)
        os.environ["ADMIN_KEY"] = admin_key
        log.warning(
            "No ADMIN_KEY set — generated one for this session:\n"
            "  http://localhost:8000/?admin_key=%s",
            admin_key,
        )
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="FreshPowder", lifespan=lifespan)
    app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    app.include_router(invite_router)
    app.include_router(admin_router)
    app.include_router(event_router)
    app.include_router(router)
    return app
