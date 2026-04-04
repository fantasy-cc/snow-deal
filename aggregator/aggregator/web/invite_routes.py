"""Invite code entry routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from aggregator.auth import (
    SESSION_COOKIE,
    create_session_token,
    is_public_mode,
)
from aggregator.auth_db import validate_invite_code, record_code_use
from aggregator.web.rate_limit import SlidingWindowRateLimiter, client_key

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

invite_router = APIRouter()
INVITE_SUBMIT_LIMIT = 10
INVITE_WINDOW_SECONDS = 300
invite_submit_limiter = SlidingWindowRateLimiter(window_seconds=INVITE_WINDOW_SECONDS)


@invite_router.get("/invite", response_class=HTMLResponse)
async def invite_page(request: Request):
    if is_public_mode():
        return RedirectResponse(url="/", status_code=302)
    return templates.TemplateResponse(
        request=request, name="invite.html", context={"error": None},
    )


@invite_router.post("/invite", response_class=HTMLResponse)
async def invite_submit(request: Request, code: str = Form(...)):
    if is_public_mode():
        return RedirectResponse(url="/", status_code=302)
    if not invite_submit_limiter.allow(
        client_key(request, "invite-submit"), INVITE_SUBMIT_LIMIT
    ):
        return templates.TemplateResponse(
            request=request,
            name="invite.html",
            context={"error": "Too many invite attempts. Please wait a few minutes and try again."},
            status_code=429,
        )
    code = code.strip().upper()
    valid = await validate_invite_code(code)
    if not valid:
        return templates.TemplateResponse(
            request=request, name="invite.html",
            context={"error": "Invalid or exhausted invite code."},
        )
    # Record the use for tracking, then issue a JWT
    await record_code_use(code)
    token = create_session_token(code)
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, max_age=86400 * 365)
    return response
