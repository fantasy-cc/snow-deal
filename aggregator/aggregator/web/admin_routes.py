"""Admin routes for managing invite codes."""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from aggregator.auth import require_invite
from aggregator.auth_db import create_invite_codes, list_invite_codes

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

admin_router = APIRouter(prefix="/admin")


async def _require_admin(request: Request) -> bool:
    """Return True if the request is from an admin."""
    session = await require_invite(request)
    return session == "admin"


@admin_router.get("/codes", response_class=HTMLResponse)
async def admin_codes_page(request: Request):
    if not await _require_admin(request):
        return RedirectResponse(url="/invite", status_code=302)
    codes = await list_invite_codes()
    return templates.TemplateResponse(
        request=request, name="admin_codes.html",
        context={"codes": codes, "max_uses": 5},
    )


@admin_router.post("/codes", response_class=HTMLResponse)
async def admin_create_codes(request: Request, count: int = Form(5)):
    if not await _require_admin(request):
        return RedirectResponse(url="/invite", status_code=302)
    count = min(count, 50)  # cap at 50
    new_codes = [secrets.token_hex(4).upper() for _ in range(count)]
    await create_invite_codes(new_codes)
    codes = await list_invite_codes()
    return templates.TemplateResponse(
        request=request,
        name="admin_codes.html",
        context={"codes": codes, "new_codes": new_codes, "max_uses": 5},
    )
