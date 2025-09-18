from pydantic import BaseModel
from typing import Optional

class ItemIn(BaseModel):
    sku: str
    name: str
    barcode: Optional[str]
    price: float

class ItemOut(ItemIn):
    id: int

class CompetitorOut(BaseModel):
    id: int
    code: str
    name: str

class MatchOut(BaseModel):
    id: int
    item_id: int
    competitor_product_id: int
    auto_by_barcode: bool
    approved: bool

class TagIn(BaseModel):
    name: str
    email: Optional[str] = None

class TagOut(TagIn):
    id: int

class ItemTagIn(BaseModel):
    item_id: int
    tag_id: int

class PriceCompareRow(BaseModel):
    our_sku: str
    comp_sku: Optional[str]
    our_name: str
    comp_name: Optional[str]
    our_price: float
    comp_price: Optional[float]
    diff: Optional[float] = None
