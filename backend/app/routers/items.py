from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from .. import models
from ..schemas import ItemIn, ItemOut

router = APIRouter(prefix="/items", tags=["items"])


@router.post("/upsert", response_model=dict)
async def upsert(items: list[ItemIn], session: AsyncSession = Depends(get_session)):
    # simple upsert by SKU
    for i in items:
        res = await session.execute(
            select(models.Item).where(models.Item.sku == i.sku)
        )
        row = res.scalar_one_or_none()
        if row:
            row.name = i.name
            row.barcode = i.barcode
            row.price = i.price
        else:
            session.add(
                models.Item(
                    sku=i.sku,
                    name=i.name,
                    barcode=i.barcode,
                    price=i.price,
                )
            )
    await session.commit()
    return {"status": "ok", "count": len(items)}


@router.get("/", response_model=list[ItemOut])
async def list_items(session: AsyncSession = Depends(get_session)):
    res = await session.execute(
        select(models.Item).order_by(models.Item.id.desc()).limit(1000)
    )
    items = res.scalars().all()
    return [
        ItemOut(id=o.id, sku=o.sku, name=o.name, barcode=o.barcode, price=o.price)
        for o in items
    ]
