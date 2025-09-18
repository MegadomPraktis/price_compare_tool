from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pathlib

from .config import settings
from .db import Base, engine, SessionLocal
from . import models
from .routers import items, match, compare, tags, schedules
from .services.excel import write_comparison_xlsx
from .services.emailer import send_email_with_attachment


app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.CORS_ORIGINS.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(items.router)
app.include_router(match.router)
app.include_router(compare.router)
app.include_router(tags.router)
app.include_router(schedules.router)

# Serve frontend build from /ui
FRONTEND_DIST = pathlib.Path(__file__).resolve().parents[1].parent / "frontend" / "dist"
print("Serving UI from:", FRONTEND_DIST)  # add this log

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

@app.get("/ui")
async def ui_root():
    # If someone hits /ui without slash, redirect to /ui/
    return RedirectResponse(url="/ui/")
# Scheduler
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def on_start():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # seed competitor praktiker
    async with SessionLocal() as s:  # type: AsyncSession
        q = await s.execute(
            select(models.Competitor).where(models.Competitor.code == "praktiker")
        )
        if not q.scalar_one_or_none():
            s.add(
                models.Competitor(
                    code="praktiker",
                    name="Praktiker",
                    base_url="https://praktiker.bg",
                )
            )
            await s.commit()

    # load schedules from DB
    await refresh_schedules()
    scheduler.start()

async def refresh_schedules():
    scheduler.remove_all_jobs()
    async with SessionLocal() as s:  # type: AsyncSession
        res = await s.execute(
            select(models.EmailSchedule, models.Tag)
            .join(models.Tag, models.Tag.id == models.EmailSchedule.tag_id)
            .where(models.EmailSchedule.active == True)
        )
        for sch, tag in res.all():
            scheduler.add_job(
                run_email_job,
                CronTrigger.from_crontab(sch.cron),
                kwargs={"tag_id": tag.id},
                id=f"email_tag_{tag.id}_{sch.id}",
                replace_existing=True,
            )

async def run_email_job(tag_id: int):
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
                .join(models.CompetitorProduct, models.CompetitorProduct.id == models.Match.competitor_product_id)
                .where(
                    models.Match.item_id == it.id,
                    models.Match.approved == True,
                    models.CompetitorProduct.competitor_id == comp.id
                )
            )
            mm = q_match.first()
            rows.append({
                "our_sku": it.sku,
                "comp_sku": mm[1].sku if mm else None,
                "our_name": it.name,
                "comp_name": mm[1].name if mm else None,
                "our_price": it.price,
                "comp_price": None,
                "diff": None,
            })

        path = write_comparison_xlsx(rows, f"/tmp/pricecompare_tag_{tag_id}.xlsx")
        tag = (await s.execute(select(models.Tag).where(models.Tag.id == tag_id))).scalar_one()
        if tag.email:
            send_email_with_attachment(
                tag.email,
                "Price comparison",
                "Attached is your comparison.",
                path,
            )

@app.get("/health")
async def health():
    return {"status": "ok"}
