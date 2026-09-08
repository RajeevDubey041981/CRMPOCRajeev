"""Extend item_masters with product fields

Revision ID: 0005_item_master_extend
Revises: 0004_projects_workflow
Create Date: 2026-05-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_item_master_extend"
down_revision: Union[str, None] = "0004_projects_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("item_masters", sa.Column("description", sa.Text, nullable=True))
    op.add_column("item_masters", sa.Column("brand", sa.String(100), nullable=True))
    op.add_column("item_masters", sa.Column("unit", sa.String(50), nullable=True))
    op.add_column("item_masters", sa.Column("hsn_code", sa.String(20), nullable=True))
    op.add_column("item_masters", sa.Column("mrp", sa.Numeric(10, 2), nullable=True))
    op.add_column(
        "item_masters",
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
    )


def downgrade() -> None:
    op.drop_column("item_masters", "is_active")
    op.drop_column("item_masters", "mrp")
    op.drop_column("item_masters", "hsn_code")
    op.drop_column("item_masters", "unit")
    op.drop_column("item_masters", "brand")
    op.drop_column("item_masters", "description")
