from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import get_session
from .. import models
from ..schemas import PriceCompareRow

router = APIRouter(prefix="/compare", tags=["compare"])


@router.get("/{competitor_code}", response_model=list[PriceCompareRow])
async def compare(competitor_code: str, session: AsyncSession = Depends(get_session)):
    comp = (
        await session.execute(
            select(models.Competitor).where(models.Competitor.code == competitor_code)
        )
    ).scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found")

    q = await session.execute(
        select(models.Match, models.Item, models.CompetitorProduct)
        .join(models.Item, models.Item.id == models.Match.item_id)
        .join(
            models.CompetitorProduct,
            models.CompetitorProduct.id == models.Match.competitor_product_id,
        )
        .where(
            models.Match.approved.is_(True),
            models.CompetitorProduct.competitor_id == comp.id,
        )
    )
    rows: list[PriceCompareRow] = []
    for m, it, cp in q.all():
        rows.append(
            PriceCompareRow(
                our_sku=it.sku,
                comp_sku=cp.sku,
                our_name=it.name,
                comp_name=cp.name,
                our_price=it.price,
                comp_price=None,  # could live-scrape here
                diff=None,
            )
        )
    return rows
