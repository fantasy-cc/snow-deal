"""Invite code entry routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from aggregator.auth import SESSION_COOKIE, create_session_token
from aggregator.auth_db import validate_invite_code, record_code_use

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

invite_router = APIRouter()


@invite_router.get("/invite", response_class=HTMLResponse)
async def invite_page(request: Request):
    return templates.TemplateResponse(
        request=request, name="invite.html", context={"error": None},
    )


@invite_router.post("/invite", response_class=HTMLResponse)
async def invite_submit(request: Request, code: str = Form(...)):
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
