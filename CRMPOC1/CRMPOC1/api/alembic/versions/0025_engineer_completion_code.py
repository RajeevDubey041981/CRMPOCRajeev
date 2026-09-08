"""Add engineer completion code on service completions

Revision ID: 0025_engineer_completion_code
Revises: 0024_service_completion_code
Create Date: 2026-08-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0025_engineer_completion_code"
down_revision: Union[str, None] = "0024_service_completion_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_completions",
        sa.Column("engineer_completion_code", sa.String(length=10), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("service_completions", "engineer_completion_code")
