from __future__ import annotations

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

# -------------------------
# Item
# -------------------------

class ItemIn(BaseModel):
    sku: str = Field(..., min_length=1, max_length=64)
    name: str                       # Cyrillic OK
    barcode: Optional[str] = Field(default=None, max_length=64)
    price: float = Field(ge=0)

class ItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    barcode: Optional[str]
    price: float
    created_at: datetime

# -------------------------
# Tag
# -------------------------

class TagIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    email: Optional[str] = Field(default=None, max_length=256)

class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: Optional[str]
    created_at: datetime

# -------------------------
# Match (optional response)
# -------------------------

class MatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    competitor_product_id: int
    approved: bool
    auto_by_barcode: bool
    created_at: datetime

# -------------------------
# Competitor Product (minimal)
# -------------------------

class CompetitorProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    competitor_id: int
    sku: str
    name: str
    url: str
    barcode: Optional[str]
    created_at: datetime

# -------------------------
# Price comparison row (used by routers/compare.py)
# -------------------------

class PriceCompareRow(BaseModel):
    """
    One row in the price comparison view.
    """
    model_config = ConfigDict(from_attributes=True)

    our_sku: str
    comp_sku: Optional[str] = None
    our_name: str
    comp_name: Optional[str] = None
    our_price: float
    comp_price: Optional[float] = None
    diff: Optional[float] = None
    comp_url: Optional[str] = None
