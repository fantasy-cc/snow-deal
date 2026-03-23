"""Invite-only authentication middleware."""

from __future__ import annotations

import os

from fastapi import Request, Response
from fastapi.responses import RedirectResponse

from aggregator.db import validate_session

ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
SESSION_COOKIE = "snow_deals_session"

# Paths that don't require authentication
PUBLIC_PATHS = {"/invite", "/static", "/admin", "/api/event"}


def _is_public(path: str) -> bool:
    return any(path.startswith(p) for p in PUBLIC_PATHS)


async def require_invite(request: Request) -> str | None:
    """Check if the request has a valid session. Returns session token or None.

    Used as a FastAPI dependency — but auth enforcement is done via middleware
    so we can redirect rather than raise 403.
    """
    # Admin bypass via env var
    if ADMIN_KEY:
        if request.cookies.get("admin_key") == ADMIN_KEY:
            return "admin"
        if request.query_params.get("admin_key") == ADMIN_KEY:
            return "admin"

    token = request.cookies.get(SESSION_COOKIE)
    if token and await validate_session(token):
        return token
    return None


def _maybe_set_admin_cookie(request: Request, response: Response) -> None:
    """Set admin_key cookie if authenticated via query param but cookie not yet set."""
    if ADMIN_KEY and not request.cookies.get("admin_key"):
        admin_key = request.query_params.get("admin_key")
        if admin_key == ADMIN_KEY:
            response.set_cookie("admin_key", admin_key, httponly=True, max_age=86400 * 365)


async def auth_middleware(request: Request, call_next):
    """Middleware that enforces invite-only access."""
    if _is_public(request.url.path):
        response = await call_next(request)
        _maybe_set_admin_cookie(request, response)
        return response

    session = await require_invite(request)
    if session:
        response = await call_next(request)
        if session == "admin":
            _maybe_set_admin_cookie(request, response)
        return response

    return RedirectResponse(url="/invite", status_code=302)
