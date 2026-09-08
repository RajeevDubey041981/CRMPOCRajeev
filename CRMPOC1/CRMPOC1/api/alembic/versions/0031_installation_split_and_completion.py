"""Split call-center installations per verified serial and track parent linkage.

Revision ID: 0031_installation_split_and_completion
Revises: 0030_installation_engineer_serials
Create Date: 2026-08-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0031_installation_split_and_completion"
down_revision: Union[str, None] = "0030_installation_engineer_serials"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "installation_requests",
        sa.Column("parent_installation_id", sa.Integer(), sa.ForeignKey("installation_requests.id"), nullable=True),
    )
    op.create_index(
        "ix_installation_requests_parent_installation_id",
        "installation_requests",
        ["parent_installation_id"],
    )
    op.add_column(
        "installation_engineer_serials",
        sa.Column(
            "split_installation_request_id",
            sa.Integer(),
            sa.ForeignKey("installation_requests.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("installation_engineer_serials", "split_installation_request_id")
    op.drop_index("ix_installation_requests_parent_installation_id", table_name="installation_requests")
    op.drop_column("installation_requests", "parent_installation_id")
