"""Engineer serial lines with observations for call-center installations.

Revision ID: 0030_installation_engineer_serials
Revises: 0029_installation_complaint_id
Create Date: 2026-08-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0030_installation_engineer_serials"
down_revision: Union[str, None] = "0029_installation_complaint_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("installation_requests", sa.Column("engineer_site_remarks", sa.Text(), nullable=True))
    op.add_column("installation_requests", sa.Column("engineer_serials_submitted_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "installation_engineer_serials",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("installation_request_id", sa.Integer(), sa.ForeignKey("installation_requests.id"), nullable=False),
        sa.Column("line_no", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("serial_no", sa.String(length=100), nullable=False),
        sa.Column("serial_no_2", sa.String(length=100), nullable=True),
        sa.Column("observation", sa.Text(), nullable=True),
        sa.Column("unit_status", sa.String(length=50), nullable=True),
        sa.Column("verification_status", sa.String(length=50), nullable=False, server_default="Pending"),
        sa.Column("admin_remark", sa.Text(), nullable=True),
        sa.Column("verified_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_installation_engineer_serials_installation_request_id",
        "installation_engineer_serials",
        ["installation_request_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_installation_engineer_serials_installation_request_id", table_name="installation_engineer_serials")
    op.drop_table("installation_engineer_serials")
    op.drop_column("installation_requests", "engineer_serials_submitted_at")
    op.drop_column("installation_requests", "engineer_site_remarks")
