"""Add dedicated installation payment proof field.

Revision ID: 0014_installation_payment_proof
Revises: 0013_installation_payment_flow
Create Date: 2026-08-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0014_installation_payment_proof"
down_revision: Union[str, None] = "0013_installation_payment_flow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("installation_requests", sa.Column("payment_proof_file_path", sa.String(length=500), nullable=True))


def downgrade() -> None:
    op.drop_column("installation_requests", "payment_proof_file_path")
