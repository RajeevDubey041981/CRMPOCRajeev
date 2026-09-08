"""Add serial_count to item_masters

Revision ID: 0020_item_master_serial_count
Revises: 0019_link_service_requests_to_complaints
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020_item_master_serial_count"
down_revision: Union[str, None] = "0019_link_service_requests_to_complaints"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "item_masters",
        sa.Column("serial_count", sa.Integer(), nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_column("item_masters", "serial_count")
