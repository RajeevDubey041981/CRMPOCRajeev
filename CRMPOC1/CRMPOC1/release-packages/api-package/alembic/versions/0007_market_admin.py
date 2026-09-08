"""Market Admin subsystem — categories, items, users, orders, order items

Revision ID: 0007_market_admin
Revises: 0006_claim_extend
Create Date: 2026-05-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_market_admin"
down_revision: Union[str, None] = "0006_claim_extend"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # market_categories
    op.create_table(
        "market_categories",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_id", sa.Integer, sa.ForeignKey("market_categories.id"), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # market_items
    op.create_table(
        "market_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("company", sa.String(100), nullable=True),
        sa.Column("category_id", sa.Integer, sa.ForeignKey("market_categories.id"), nullable=True),
        sa.Column("base_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("mrp", sa.Numeric(10, 2), nullable=True),
        sa.Column("image_path", sa.String(500), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="Active"),
        sa.Column("stock_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_market_items_sku", "market_items", ["sku"], unique=True)

    # market_users
    op.create_table(
        "market_users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),
        sa.Column("address", sa.Text, nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("role", sa.String(50), nullable=False, server_default="Retailer"),
        sa.Column("status", sa.String(20), nullable=False, server_default="Pending"),
        sa.Column("fee_status", sa.String(20), nullable=False, server_default="Pending"),
        sa.Column("onboarding_fee", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "joined_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_market_users_email", "market_users", ["email"], unique=True)

    # market_orders
    op.create_table(
        "market_orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("order_no", sa.String(50), nullable=False),
        sa.Column("retailer_id", sa.Integer, sa.ForeignKey("market_users.id"), nullable=True),
        sa.Column("distributor_id", sa.Integer, sa.ForeignKey("market_users.id"), nullable=True),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="Pending"),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_market_orders_order_no", "market_orders", ["order_no"], unique=True)

    # market_order_items
    op.create_table(
        "market_order_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "order_id",
            sa.Integer,
            sa.ForeignKey("market_orders.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("market_items.id"), nullable=True),
        sa.Column("qty", sa.Integer, nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("subtotal", sa.Numeric(12, 2), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_market_order_items_order_id", "market_order_items", ["order_id"])


def downgrade() -> None:
    op.drop_table("market_order_items")
    op.drop_table("market_orders")
    op.drop_table("market_users")
    op.drop_table("market_items")
    op.drop_table("market_categories")
