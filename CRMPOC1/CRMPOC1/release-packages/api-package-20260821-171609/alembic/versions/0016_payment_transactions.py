"""Add payment transactions for grouped payment history.

Revision ID: 0016_payment_transactions
Revises: 0015_installation_qr_blob_storage
Create Date: 2026-08-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0016_payment_transactions"
down_revision: Union[str, None] = "0015_installation_qr_blob_storage"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "payment_transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("payment_type", sa.String(length=20), nullable=False),
        sa.Column("total_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("recorded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("engineer_user_id", sa.Integer(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["recorded_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["engineer_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.add_column("installation_requests", sa.Column("payment_transaction_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_installation_requests_payment_transaction_id",
        "installation_requests",
        "payment_transactions",
        ["payment_transaction_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_installation_requests_payment_transaction_id", "installation_requests", type_="foreignkey")
    op.drop_column("installation_requests", "payment_transaction_id")
    op.drop_table("payment_transactions")
