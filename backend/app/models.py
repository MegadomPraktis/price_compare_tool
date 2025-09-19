from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import Unicode, UnicodeText

from .db import Base


# -------------------------
# Core tables
# -------------------------

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    sku: Mapped[str] = mapped_column(Unicode(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(UnicodeText)  # Cyrillic-safe
    barcode: Mapped[Optional[str]] = mapped_column(Unicode(64), index=True, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.sysutcdatetime(),  # SQL Server DATETIME2 UTC
        nullable=False,
    )

    matches: Mapped[List["Match"]] = relationship(back_populates="item", cascade="all, delete-orphan")
    tags: Mapped[List["ItemTag"]] = relationship(back_populates="item", cascade="all, delete-orphan")


class Competitor(Base):
    __tablename__ = "competitors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Unicode(32), unique=True, index=True)  # e.g., "praktiker"
    name: Mapped[str] = mapped_column(Unicode(128))
    base_url: Mapped[str] = mapped_column(Unicode(256))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.sysutcdatetime(),
        nullable=False,
    )

    products: Mapped[List["CompetitorProduct"]] = relationship(
        back_populates="competitor", cascade="all, delete-orphan"
    )


class CompetitorProduct(Base):
    __tablename__ = "competitor_products"
    __table_args__ = (
        UniqueConstraint("competitor_id", "sku", name="uq_competitor_sku"),
        # NOTE: keep the composite index by relying on the individual column
        # indexes for lookups; add a composite one later with Alembic if needed.
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    competitor_id: Mapped[int] = mapped_column(ForeignKey("competitors.id", ondelete="CASCADE"), index=True)
    sku: Mapped[str] = mapped_column(Unicode(64), index=True)
    name: Mapped[str] = mapped_column(UnicodeText)
    url: Mapped[str] = mapped_column(Unicode(512))
    barcode: Mapped[Optional[str]] = mapped_column(Unicode(64), index=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.sysutcdatetime(),
        nullable=False,
    )

    competitor: Mapped["Competitor"] = relationship(back_populates="products")
    matches: Mapped[List["Match"]] = relationship(
        back_populates="competitor_product", cascade="all, delete-orphan"
    )


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("item_id", "competitor_product_id", name="uq_item_competitor_product"),
        # removed explicit Index("ix_matches_item_id", "item_id")
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), index=True)
    competitor_product_id: Mapped[int] = mapped_column(
        ForeignKey("competitor_products.id", ondelete="CASCADE"), index=True
    )
    approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_by_barcode: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.sysutcdatetime(),
        nullable=False,
    )

    item: Mapped["Item"] = relationship(back_populates="matches")
    competitor_product: Mapped["CompetitorProduct"] = relationship(back_populates="matches")


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("name", name="uq_tags_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Unicode(128), index=True)  # Cyrillic-safe
    email: Mapped[Optional[str]] = mapped_column(Unicode(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.sysutcdatetime(),
        nullable=False,
    )

    item_links: Mapped[List["ItemTag"]] = relationship(back_populates="tag", cascade="all, delete-orphan")
    schedules: Mapped[List["EmailSchedule"]] = relationship(back_populates="tag", cascade="all, delete-orphan")


class ItemTag(Base):
    __tablename__ = "item_tags"
    __table_args__ = (
        UniqueConstraint("item_id", "tag_id", name="uq_item_tag"),
        # removed explicit Index("ix_item_tags_item_id", "item_id")
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("items.id", ondelete="CASCADE"), index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.sysutcdatetime(),
        nullable=False,
    )

    item: Mapped["Item"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship(back_populates="item_links")


class EmailSchedule(Base):
    __tablename__ = "email_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="CASCADE"), index=True)
    cron: Mapped[str] = mapped_column(Unicode(64))  # crontab string
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.sysutcdatetime(),
        nullable=False,
    )

    tag: Mapped["Tag"] = relationship(back_populates="schedules")
