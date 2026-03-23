"""Invite code entry routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from aggregator.auth import SESSION_COOKIE
from aggregator.db import redeem_invite_code

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

invite_router = APIRouter()


@invite_router.get("/invite", response_class=HTMLResponse)
async def invite_page(request: Request):
    return templates.TemplateResponse("invite.html", {"request": request, "error": None})


@invite_router.post("/invite", response_class=HTMLResponse)
async def invite_submit(request: Request, code: str = Form(...)):
    token = await redeem_invite_code(code.strip().upper())
    if not token:
        return templates.TemplateResponse(
            "invite.html",
            {"request": request, "error": "Invalid or already-used invite code."},
        )
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(SESSION_COOKIE, token, httponly=True, max_age=86400 * 365)
    return response
