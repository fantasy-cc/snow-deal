"""Authentication helpers and middleware for public/invite-gated access."""

from __future__ import annotations

import os

import jwt
from fastapi import Request, Response
from fastapi.responses import RedirectResponse

SESSION_COOKIE = "snow_deals_session"

# Paths that don't require authentication
PUBLIC_PATHS = {"/invite", "/static", "/admin", "/api/event", "/robots.txt"}


def _env_flag(name: str, default: bool = False) -> bool:
    """Parse a boolean-like environment variable."""
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def is_public_mode() -> bool:
    """Return True when invite auth is disabled for public access."""
    return _env_flag("PUBLIC_MODE", default=False)


def get_admin_key() -> str:
    """Return the configured admin key, if any."""
    return os.environ.get("ADMIN_KEY", "")


def get_secret_key(required: bool = True) -> str:
    """Return the JWT signing key, optionally enforcing configuration."""
    secret = os.environ.get("SECRET_KEY", "").strip()
    if secret:
        return secret
    if required and not is_public_mode():
        raise RuntimeError(
            "SECRET_KEY must be set when PUBLIC_MODE is disabled."
        )
    return ""


def auth_redirect_path() -> str:
    """Redirect unauthenticated users to the appropriate landing page."""
    return "/" if is_public_mode() else "/invite"


def ensure_auth_config() -> None:
    """Validate auth-related configuration during app startup."""
    get_secret_key(required=not is_public_mode())


def _is_public(path: str) -> bool:
    return any(path.startswith(p) for p in PUBLIC_PATHS)


def create_session_token(invite_code: str) -> str:
    """Create a signed JWT containing the invite code."""
    from datetime import datetime, timezone
    secret_key = get_secret_key()
    payload = {
        "sub": invite_code,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_session_token(token: str) -> str | None:
    """Verify a JWT session token. Returns the invite code or None."""
    try:
        payload = jwt.decode(token, get_secret_key(), algorithms=["HS256"])
        return payload.get("sub")
    except (RuntimeError, jwt.InvalidTokenError, jwt.DecodeError):
        return None


async def require_invite(request: Request) -> str | None:
    """Check if the request has a valid session.

    Returns "admin" for admin users, the invite code for JWT sessions, or None.
    """
    # Admin bypass via env var
    admin_key = get_admin_key()
    if admin_key:
        if request.cookies.get("admin_key") == admin_key:
            return "admin"
        if request.query_params.get("admin_key") == admin_key:
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
    admin_key = get_admin_key()
    if admin_key and not request.cookies.get("admin_key"):
        admin_key = request.query_params.get("admin_key")
        if admin_key == get_admin_key():
            response.set_cookie("admin_key", admin_key, httponly=True, max_age=86400 * 365)


async def auth_middleware(request: Request, call_next):
    """Middleware that enforces invite-only access unless public mode is enabled."""
    if is_public_mode() or _is_public(request.url.path):
        response = await call_next(request)
        _maybe_set_admin_cookie(request, response)
        return response

    session = await require_invite(request)
    if session:
        response = await call_next(request)
        if session == "admin":
            _maybe_set_admin_cookie(request, response)
        return response

    return RedirectResponse(url=auth_redirect_path(), status_code=302)
