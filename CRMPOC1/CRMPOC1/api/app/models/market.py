from decimal import Decimal
from datetime import datetime

from sqlalchemy import String, Text, Boolean, Numeric, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base
from app.models._mixins import TimestampMixin


class MarketCategory(Base, TimestampMixin):
    __tablename__ = "market_categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_categories.id"), nullable=True
    )


class MarketItem(Base, TimestampMixin):
    __tablename__ = "market_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_categories.id"), nullable=True
    )
    base_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    mrp: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="Active"
    )
    stock_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)


class MarketUser(Base, TimestampMixin):
    __tablename__ = "market_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default="Retailer"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="Pending"
    )
    fee_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="Pending"
    )
    onboarding_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class MarketOrder(Base, TimestampMixin):
    __tablename__ = "market_orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_no: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    retailer_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_users.id"), nullable=True
    )
    distributor_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_users.id"), nullable=True
    )
    total_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="Pending"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MarketOrderItem(Base, TimestampMixin):
    __tablename__ = "market_order_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("market_orders.id", ondelete="CASCADE"), nullable=False
    )
    item_id: Mapped[int | None] = mapped_column(
        ForeignKey("market_items.id"), nullable=True
    )
    qty: Mapped[int] = mapped_column(Integer, nullable=False, server_default="1")
    unit_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    subtotal: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
