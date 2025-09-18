from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint, Float, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from .db import Base

class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(String(64), index=True, unique=True)
    name: Mapped[str] = mapped_column(Text)
    barcode: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    price: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    matches: Mapped[list["Match"]] = relationship(back_populates="item")
    tags: Mapped[list["ItemTag"]] = relationship(back_populates="item")

class Competitor(Base):
    __tablename__ = "competitors"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(128))
    base_url: Mapped[str] = mapped_column(String(256))

class CompetitorProduct(Base):
    __tablename__ = "competitor_products"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id"))
    sku: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(String(512))
    barcode: Mapped[str | None] = mapped_column(String(64), index=True)

    __table_args__ = (UniqueConstraint("competitor_id", "sku", name="uq_competitor_sku"),)

class Match(Base):
    __tablename__ = "matches"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    competitor_product_id: Mapped[int] = mapped_column(ForeignKey("competitor_products.id"))
    auto_by_barcode: Mapped[bool] = mapped_column(Boolean, default=False)
    approved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    item: Mapped["Item"] = relationship(back_populates="matches")

class PriceSnapshot(Base):
    __tablename__ = "price_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"))
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id"))
    item_price: Mapped[float] = mapped_column(Float)
    competitor_price: Mapped[float | None] = mapped_column(Float)
    taken_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

class Tag(Base):
    __tablename__ = "tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), unique=True)
    email: Mapped[str | None] = mapped_column(String(256))

class ItemTag(Base):
    __tablename__ = "item_tags"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id"), index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), index=True)

    item: Mapped["Item"] = relationship(back_populates="tags")

class EmailSchedule(Base):
    __tablename__ = "email_schedules"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"))
    cron: Mapped[str] = mapped_column(String(64))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
