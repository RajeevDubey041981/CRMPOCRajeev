"""Extend claims table with bank/settlement fields

Revision ID: 0006_claim_extend
Revises: 0005_item_master_extend
Create Date: 2026-05-30

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_claim_extend"
down_revision: Union[str, None] = "0005_item_master_extend"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("claims", sa.Column("bank_name", sa.String(100), nullable=True))
    op.add_column("claims", sa.Column("account_holder_name", sa.String(255), nullable=True))
    op.add_column("claims", sa.Column("account_number", sa.String(100), nullable=True))
    op.add_column("claims", sa.Column("ifsc_code", sa.String(20), nullable=True))
    op.add_column("claims", sa.Column("admin_remark", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("claims", "admin_remark")
    op.drop_column("claims", "ifsc_code")
    op.drop_column("claims", "account_number")
    op.drop_column("claims", "account_holder_name")
    op.drop_column("claims", "bank_name")
