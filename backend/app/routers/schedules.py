from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from .. import models

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.post("/", response_model=dict)
async def create_schedule(
    tag_id: int,
    cron: str,
    session: AsyncSession = Depends(get_session),
):
    s = models.EmailSchedule(tag_id=tag_id, cron=cron, active=True)
    session.add(s)
    await session.commit()
    return {"id": s.id, "status": "ok"}


@router.get("/", response_model=list[dict])
async def list_schedules(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(models.EmailSchedule))
    return [
        {"id": s.id, "tag_id": s.tag_id, "cron": s.cron, "active": s.active}
        for s in res.scalars().all()
    ]
