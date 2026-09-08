"""Add serial_no/serial_no_2 to installation_requests

Revision ID: 0008_installation_serials
Revises: 0007_market_admin
Create Date: 2026-07-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_installation_serials"
down_revision: Union[str, None] = "0007_market_admin"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("installation_requests", sa.Column("serial_no", sa.String(100), nullable=True))
    op.add_column("installation_requests", sa.Column("serial_no_2", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("installation_requests", "serial_no_2")
    op.drop_column("installation_requests", "serial_no")
