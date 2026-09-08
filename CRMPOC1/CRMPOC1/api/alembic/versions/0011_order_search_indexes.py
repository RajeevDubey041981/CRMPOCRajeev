"""Add indexes for order autocomplete search.

Revision ID: 0011_order_search_indexes
Revises: 0010_order_item_item_code
Create Date: 2026-08-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0011_order_search_indexes"
down_revision: Union[str, None] = "0010_order_item_item_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(op.f("ix_orders_customer_contact"), "orders", ["customer_contact"], unique=False)
    op.create_index(op.f("ix_orders_customer_name"), "orders", ["customer_name"], unique=False)
    op.create_index(op.f("ix_orders_oem_bill_no"), "orders", ["oem_bill_no"], unique=False)
    op.create_index(op.f("ix_vendors_name_of_firm"), "vendors", ["name_of_firm"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_vendors_name_of_firm"), table_name="vendors")
    op.drop_index(op.f("ix_orders_oem_bill_no"), table_name="orders")
    op.drop_index(op.f("ix_orders_customer_name"), table_name="orders")
    op.drop_index(op.f("ix_orders_customer_contact"), table_name="orders")
