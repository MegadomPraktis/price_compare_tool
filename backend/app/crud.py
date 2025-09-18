from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from . import models

async def upsert_items(session: AsyncSession, items: list[dict]):
    for it in items:
        res = await session.execute(select(models.Item).where(models.Item.sku == it["sku"]))
        row = res.scalar_one_or_none()
        if row:
            row.name = it["name"]
            row.barcode = it.get("barcode")
            row.price = it["price"]
        else:
            session.add(models.Item(**it))
    await session.commit()

async def create_tag(session: AsyncSession, name: str, email: str | None):
    tag = models.Tag(name=name, email=email)
    session.add(tag)
    await session.commit()
    await session.refresh(tag)
    return tag
