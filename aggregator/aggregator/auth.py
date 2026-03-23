"""Invite-only authentication middleware with JWT sessions."""

from __future__ import annotations

import os

import jwt
from fastapi import Request, Response
from fastapi.responses import RedirectResponse

ADMIN_KEY = os.environ.get("ADMIN_KEY", "")
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")
SESSION_COOKIE = "snow_deals_session"

# Paths that don't require authentication
PUBLIC_PATHS = {"/invite", "/static", "/admin", "/api/event"}


def _is_public(path: str) -> bool:
    return any(path.startswith(p) for p in PUBLIC_PATHS)


def create_session_token(invite_code: str) -> str:
    """Create a signed JWT containing the invite code."""
    from datetime import datetime, timezone
    payload = {
        "sub": invite_code,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def verify_session_token(token: str) -> str | None:
    """Verify a JWT session token. Returns the invite code or None."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except (jwt.InvalidTokenError, jwt.DecodeError):
        return None


async def require_invite(request: Request) -> str | None:
    """Check if the request has a valid session.

    Returns "admin" for admin users, the invite code for JWT sessions, or None.
    """
    # Admin bypass via env var
    if ADMIN_KEY:
        if request.cookies.get("admin_key") == ADMIN_KEY:
            return "admin"
        if request.query_params.get("admin_key") == ADMIN_KEY:
            return "admin"

    # JWT session cookie
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        invite_code = verify_session_token(token)
        if invite_code:
            return invite_code
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
