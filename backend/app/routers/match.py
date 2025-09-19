from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app import models
from app.services.matcher import auto_match_by_barcode
from app.services import scraper_praktiker

router = APIRouter(prefix="/match", tags=["match"])

@router.post("/auto/{competitor_code}", response_model=dict)
async def auto_match_all(competitor_code: str, session: AsyncSession = Depends(get_session)):
    comp = (
        await session.execute(
            select(models.Competitor).where(models.Competitor.code == competitor_code)
        )
    ).scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found")

    items = (await session.execute(select(models.Item))).scalars().all()
    created = 0
    for it in items:
        m = await auto_match_by_barcode(session, comp.id, it)
        if m:
            created += 1
    return {"status": "ok", "created": created}

@router.get("/view/{competitor_code}", response_model=list[dict])
async def view_table(competitor_code: str, session: AsyncSession = Depends(get_session)):
    """
    Row per item:
      - item_id
      - our_sku
      - comp_barcode (if matched & approved for this competitor)
      - comp_url (clickable)
      - approved
    """
    comp = (
        await session.execute(
            select(models.Competitor).where(models.Competitor.code == competitor_code)
        )
    ).scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found")

    q = await session.execute(
        select(
            models.Item.id.label("item_id"),
            models.Item.sku.label("our_sku"),
            models.CompetitorProduct.barcode.label("comp_barcode"),
            models.CompetitorProduct.url.label("comp_url"),
            func.coalesce(models.Match.approved, False).label("approved"),
        )
        .select_from(models.Item)
        .join(models.Match, models.Match.item_id == models.Item.id, isouter=True)
        .join(models.CompetitorProduct, models.CompetitorProduct.id == models.Match.competitor_product_id, isouter=True)
        .where(
            (models.Match.id.is_(None)) | (models.CompetitorProduct.competitor_id == comp.id)
        )
        .order_by(models.Item.id.asc())
    )

    rows_map: dict[int, dict] = {}
    for item_id, our_sku, comp_barcode, comp_url, approved in q.all():
        cand = {
            "item_id": item_id,
            "our_sku": our_sku,
            "comp_barcode": comp_barcode,
            "comp_url": comp_url,
            "approved": bool(approved),
        }
        prev = rows_map.get(item_id)
        if prev is None or (not prev["approved"] and cand["approved"]):
            rows_map[item_id] = cand

    # Ensure every item appears
    all_items = (await session.execute(select(models.Item.id, models.Item.sku))).all()
    for item_id, sku in all_items:
        rows_map.setdefault(item_id, {
            "item_id": item_id, "our_sku": sku,
            "comp_barcode": None, "comp_url": None, "approved": False
        })

    return list(rows_map.values())

@router.post("/manual_by_barcode/{competitor_code}", response_model=dict)
async def manual_by_barcode(
    competitor_code: str,
    item_id: int,
    competitor_barcode: str,
    session: AsyncSession = Depends(get_session),
):
    """
    Manually link by competitor BARCODE: search praktiker, upsert competitor product,
    create APPROVED match.
    """
    comp = (
        await session.execute(
            select(models.Competitor).where(models.Competitor.code == competitor_code)
        )
    ).scalar_one_or_none()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found")

    item = (
        await session.execute(select(models.Item).where(models.Item.id == item_id))
    ).scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    result = await scraper_praktiker.search_by_barcode(competitor_barcode)
    if not result:
        raise HTTPException(status_code=404, detail="Competitor product not found by barcode")

    # upsert competitor product by (competitor_id, sku)
    q = await session.execute(
        select(models.CompetitorProduct).where(
            models.CompetitorProduct.competitor_id == comp.id,
            models.CompetitorProduct.sku == result["sku"],
        )
    )
    cp = q.scalar_one_or_none()
    if not cp:
        cp = models.CompetitorProduct(
            competitor_id=comp.id,
            sku=result["sku"],
            name=result["name"],
            url=result["url"],
            barcode=result.get("barcode") or competitor_barcode,
        )
        session.add(cp)
        await session.flush()

    match = models.Match(
        item_id=item.id,
        competitor_product_id=cp.id,
        auto_by_barcode=False,
        approved=True,
    )
    session.add(match)
    await session.commit()
    return {"status": "ok", "item_id": item.id, "comp_barcode": cp.barcode, "comp_url": cp.url}
