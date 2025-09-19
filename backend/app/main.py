from __future__ import annotations

import os
import pathlib
import contextlib
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .config import settings
from .db import Base, engine, SessionLocal
from . import models
from .services.excel import write_comparison_xlsx
from .services.emailer import send_email_with_attachment
from starlette.requests import Request
from starlette.responses import Response
import time

app = FastAPI(title=settings.APP_NAME)

@app.middleware("http")
async def _log_requests(request: Request, call_next):
    start = time.perf_counter()
    try:
        response: Response = await call_next(request)
        return response
    finally:
        dur_ms = int((time.perf_counter() - start) * 1000)
        print(f"{request.method} {request.url.path} -> {dur_ms}ms")

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Routers ----------
from .routers import items, match, compare, tags, schedules  # noqa: E402
app.include_router(items.router)
app.include_router(match.router)
app.include_router(compare.router)
app.include_router(tags.router)
app.include_router(schedules.router)

# ---------- Static UI ----------
FRONTEND_DIST = pathlib.Path(__file__).resolve().parents[1].parent / "frontend" / "dist"
print("Serving UI from:", FRONTEND_DIST)

if FRONTEND_DIST.exists():
    app.mount("/ui", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="ui")

    @app.get("/ui/{full_path:path}")
    async def ui_fallback(full_path: str):
        idx = FRONTEND_DIST / "index.html"
        if idx.exists():
            return FileResponse(idx)
        raise HTTPException(status_code=404, detail="UI build not found")
else:
    @app.get("/ui")
    async def ui_not_built():
        return {"detail": "UI not built yet. Run: cd frontend && npm i && npm run build"}

@app.get("/")
async def root():
    if FRONTEND_DIST.exists():
        return RedirectResponse(url="/ui")
    return {"detail": "UI not built yet. Visit /docs for API or build the UI."}

@app.get("/health")
async def health():
    return {"status": "ok"}

# ---------- Scheduler ----------
scheduler = AsyncIOScheduler()


async def _ensure_schema_and_seed() -> None:
    """Create schema if missing (idempotent) and seed competitor (upsert)."""
    print("DB: creating schema if missing …")
    async with engine.begin() as conn:
        # MetaData.create_all is already checkfirst=True internally.
        await conn.run_sync(Base.metadata.create_all)
    print("DB: schema ready.")

    # Seed competitor with merge-like behavior
    async with SessionLocal() as s:  # type: AsyncSession
        existing = await s.execute(
            select(models.Competitor).where(models.Competitor.code == "praktiker")
        )
        comp = existing.scalar_one_or_none()
        if not comp:
            s.add(
                models.Competitor(
                    code="praktiker",
                    name="Praktiker",
                    base_url="https://praktiker.bg",
                )
            )
            await s.commit()
            print("DB: seeded competitor 'praktiker'.")
        else:
            # keep name/url up to date without creating duplicates
            comp.name = "Praktiker"
            comp.base_url = "https://praktiker.bg"
            await s.commit()
            print("DB: competitor 'praktiker' up-to-date.")


async def _refresh_schedules() -> None:
    scheduler.remove_all_jobs()
    async with SessionLocal() as s:  # type: AsyncSession
        res = await s.execute(
            select(models.EmailSchedule, models.Tag)
            .join(models.Tag, models.Tag.id == models.EmailSchedule.tag_id)
            .where(models.EmailSchedule.active == True)  # noqa: E712
        )
        for sch, tag in res.all():
            scheduler.add_job(
                _run_email_job,
                CronTrigger.from_crontab(sch.cron),
                kwargs={"tag_id": tag.id},
                id=f"email_tag_{tag.id}_{sch.id}",
                replace_existing=True,
            )
    print(f"Scheduler: loaded {len(scheduler.get_jobs())} job(s).")


async def _run_email_job(tag_id: int) -> None:
    async with SessionLocal() as s:  # type: AsyncSession
        comp = (
            await s.execute(
                select(models.Competitor).where(models.Competitor.code == "praktiker")
            )
        ).scalar_one()

        q_items = await s.execute(
            select(models.Item)
            .join(models.ItemTag, models.ItemTag.item_id == models.Item.id)
            .where(models.ItemTag.tag_id == tag_id)
        )
        items = q_items.scalars().all()

        rows = []
        for it in items:
            q_match = await s.execute(
                select(models.Match, models.CompetitorProduct)
                .join(
                    models.CompetitorProduct,
                    models.CompetitorProduct.id == models.Match.competitor_product_id,
                )
                .where(
                    models.Match.item_id == it.id,
                    models.Match.approved == True,  # noqa: E712
                    models.CompetitorProduct.competitor_id == comp.id,
                )
            )
            mm = q_match.first()
            rows.append(
                {
                    "our_sku": it.sku,
                    "comp_sku": mm[1].sku if mm else None,
                    "our_name": it.name,
                    "comp_name": mm[1].name if mm else None,
                    "our_price": it.price,
                    "comp_price": None,
                    "diff": None,
                }
            )

        path = write_comparison_xlsx(rows, f"/tmp/pricecompare_tag_{tag_id}.xlsx")
        tag = (
            await s.execute(select(models.Tag).where(models.Tag.id == tag_id))
        ).scalar_one()
        if tag.email:
            send_email_with_attachment(
                tag.email,
                "Price comparison",
                "Attached is your comparison.",
                path,
            )
    print(f"Scheduler: email job for tag {tag_id} finished.")


# ---------- Lifespan (startup/shutdown) ----------
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # STARTUP
    try:
        await _ensure_schema_and_seed()
    except Exception as e:  # fail fast with a clear log
        import traceback
        print("Startup failed while ensuring schema/seeding:")
        traceback.print_exc()
        raise

    try:
        await _refresh_schedules()
        scheduler.start()
        print("Scheduler: started.")
    except Exception:
        import traceback
        print("Scheduler failed to start:")
        traceback.print_exc()
        # don’t block API if scheduler fails
    try:
        yield
    finally:
        # SHUTDOWN
        with contextlib.suppress(Exception):
            scheduler.shutdown(wait=False)
            print("Scheduler: stopped.")

# Bind lifespan to the app (overrides default events)
app.router.lifespan_context = lifespan
