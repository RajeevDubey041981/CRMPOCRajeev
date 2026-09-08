"""Add customer_state/customer_address to orders; replace order_item warranty dates with year counts

Revision ID: 0009_order_extend
Revises: 0008_installation_serials
Create Date: 2026-07-27

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009_order_extend"
down_revision: Union[str, None] = "0008_installation_serials"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("orders", sa.Column("customer_state", sa.String(100), nullable=True))
    op.add_column("orders", sa.Column("customer_address", sa.Text(), nullable=True))
    op.alter_column("orders", "order_no", existing_type=sa.String(255), nullable=True)

    op.add_column("order_items", sa.Column("item_qty", sa.Integer(), nullable=False, server_default="1"))
    op.add_column("order_items", sa.Column("pcb_warranty_years", sa.Integer(), nullable=True))
    op.add_column("order_items", sa.Column("component_warranty_years", sa.Integer(), nullable=True))
    op.add_column("order_items", sa.Column("machine_warranty_years", sa.Integer(), nullable=True))
    op.drop_column("order_items", "pcb_warranty_date")
    op.drop_column("order_items", "component_warranty_date")
    op.drop_column("order_items", "machine_warranty_date")


def downgrade() -> None:
    op.add_column("order_items", sa.Column("pcb_warranty_date", sa.Date(), nullable=True))
    op.add_column("order_items", sa.Column("component_warranty_date", sa.Date(), nullable=True))
    op.add_column("order_items", sa.Column("machine_warranty_date", sa.Date(), nullable=True))
    op.drop_column("order_items", "pcb_warranty_years")
    op.drop_column("order_items", "component_warranty_years")
    op.drop_column("order_items", "machine_warranty_years")
    op.drop_column("order_items", "item_qty")

    op.alter_column("orders", "order_no", existing_type=sa.String(255), nullable=False)
    op.drop_column("orders", "customer_address")
    op.drop_column("orders", "customer_state")
