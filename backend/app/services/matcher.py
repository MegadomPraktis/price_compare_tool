from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from . import scraper_praktiker


async def auto_match_by_barcode(
    session: AsyncSession,
    competitor_id: int,
    item: models.Item,
):
    """
    If the item has a barcode, try to find the competitor product (praktiker.bg)
    and create a Match (approved=False). Returns the Match or None.
    """
    if not item.barcode:
        return None

    res = await scraper_praktiker.search_by_barcode(item.barcode)
    if not res:
        return None

    # upsert competitor product
    q = await session.execute(
        select(models.CompetitorProduct).where(
            models.CompetitorProduct.competitor_id == competitor_id,
            models.CompetitorProduct.sku == res["sku"],
        )
    )
    cp = q.scalar_one_or_none()
    if not cp:
        cp = models.CompetitorProduct(
            competitor_id=competitor_id,
            sku=res["sku"],
            name=res["name"],
            url=res["url"],
            barcode=res.get("barcode"),
        )
        session.add(cp)
        await session.flush()

    match = models.Match(
        item_id=item.id,
        competitor_product_id=cp.id,
        auto_by_barcode=True,
        approved=False,
    )
    session.add(match)
    await session.commit()
    await session.refresh(match)
    return match
