"""Link installation requests to complaints.

Revision ID: 0029_installation_complaint_id
Revises: 0028_installation_callcenter_flow
Create Date: 2026-08-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0029_installation_complaint_id"
down_revision: Union[str, None] = "0028_installation_callcenter_flow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("installation_requests", sa.Column("complaint_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_installation_requests_complaint_id_complaints",
        "installation_requests",
        "complaints",
        ["complaint_id"],
        ["id"],
    )
    op.create_index("ix_installation_requests_complaint_id", "installation_requests", ["complaint_id"])


def downgrade() -> None:
    op.drop_index("ix_installation_requests_complaint_id", table_name="installation_requests")
    op.drop_constraint("fk_installation_requests_complaint_id_complaints", "installation_requests", type_="foreignkey")
    op.drop_column("installation_requests", "complaint_id")
