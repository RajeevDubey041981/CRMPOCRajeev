"""Add completion code (happy code) to service requests

Revision ID: 0024_service_completion_code
Revises: 0023_service_unit_lifecycle
Create Date: 2026-08-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024_service_completion_code"
down_revision: Union[str, None] = "0023_service_unit_lifecycle"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_requests",
        sa.Column("completion_code", sa.String(length=10), nullable=True),
    )
    op.create_index(
        "ix_service_requests_completion_code",
        "service_requests",
        ["completion_code"],
    )


def downgrade() -> None:
    op.drop_index("ix_service_requests_completion_code", table_name="service_requests")
    op.drop_column("service_requests", "completion_code")
