"""Event tracking routes — lightweight analytics."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from aggregator.auth import require_invite, SESSION_COOKIE
from aggregator.auth_db import log_event, get_click_stats

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATE_DIR))

event_router = APIRouter()


class EventPayload(BaseModel):
    event_type: str
    deal_url: str | None = None
    deal_name: str | None = None
    store: str | None = None
    category: str | None = None
    metadata: str | None = None


@event_router.post("/api/event")
async def track_event(request: Request, payload: EventPayload):
    """Record a user event (click, page_view, filter, search)."""
    allowed = {"click", "page_view", "filter", "search"}
    if payload.event_type not in allowed:
        return JSONResponse({"ok": False}, status_code=400)

    session = request.cookies.get(SESSION_COOKIE) or request.cookies.get("admin_key")
    await log_event(
        event_type=payload.event_type,
        session=session,
        deal_url=payload.deal_url,
        deal_name=payload.deal_name,
        store=payload.store,
        category=payload.category,
        metadata=payload.metadata,
    )
    return JSONResponse({"ok": True})


@event_router.get("/admin/stats", response_class=HTMLResponse)
async def admin_stats_page(request: Request, days: int = 7):
    """Admin dashboard showing user analytics."""
    session = await require_invite(request)
    if session != "admin":
        return RedirectResponse(url="/invite", status_code=302)

    stats = await get_click_stats(days=days)
    return templates.TemplateResponse(
        request=request, name="admin_stats.html", context={"stats": stats},
    )
