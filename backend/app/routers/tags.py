from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from .. import models
from ..schemas import TagIn, TagOut

router = APIRouter(prefix="/tags", tags=["tags"])


@router.post("/", response_model=TagOut)
async def create_tag(tag: TagIn, session: AsyncSession = Depends(get_session)):
    t = models.Tag(name=tag.name, email=tag.email)
    session.add(t)
    await session.commit()
    await session.refresh(t)
    return TagOut(id=t.id, name=t.name, email=t.email)


@router.get("/", response_model=list[TagOut])
async def list_tags(session: AsyncSession = Depends(get_session)):
    res = await session.execute(select(models.Tag))
    tags = res.scalars().all()
    return [TagOut(id=t.id, name=t.name, email=t.email) for t in tags]
