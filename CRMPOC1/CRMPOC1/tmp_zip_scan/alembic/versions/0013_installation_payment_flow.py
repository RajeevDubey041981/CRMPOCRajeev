"""Add installation payment workflow fields.

Revision ID: 0013_installation_payment_flow
Revises: 0012_serial_history_and_complaint_linkage
Create Date: 2026-08-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0013_installation_payment_flow"
down_revision: Union[str, None] = "0012_serial_history_and_complaint_linkage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("installation_requests", sa.Column("payment_amount_requested", sa.Numeric(10, 2), nullable=True))
    op.add_column("installation_requests", sa.Column("payment_type_requested", sa.String(length=20), nullable=True))
    op.add_column("installation_requests", sa.Column("payment_qr_code_path", sa.String(length=500), nullable=True))
    op.add_column("installation_requests", sa.Column("payment_requested_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("installation_requests", sa.Column("payment_amount_paid", sa.Numeric(10, 2), nullable=True))
    op.add_column("installation_requests", sa.Column("payment_type_paid", sa.String(length=20), nullable=True))
    op.add_column("installation_requests", sa.Column("payment_recorded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("installation_requests", sa.Column("payment_recorded_by", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_installation_requests_payment_recorded_by_users",
        "installation_requests",
        "users",
        ["payment_recorded_by"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_installation_requests_payment_recorded_by_users", "installation_requests", type_="foreignkey")
    op.drop_column("installation_requests", "payment_recorded_by")
    op.drop_column("installation_requests", "payment_recorded_at")
    op.drop_column("installation_requests", "payment_type_paid")
    op.drop_column("installation_requests", "payment_amount_paid")
    op.drop_column("installation_requests", "payment_requested_at")
    op.drop_column("installation_requests", "payment_qr_code_path")
    op.drop_column("installation_requests", "payment_type_requested")
    op.drop_column("installation_requests", "payment_amount_requested")
