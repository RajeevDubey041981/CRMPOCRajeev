"""Store installation payment QR codes in DB blobs.

Revision ID: 0015_installation_qr_blob_storage
Revises: 0014_installation_payment_proof
Create Date: 2026-08-08
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0015_installation_qr_blob_storage"
down_revision: Union[str, None] = "0014_installation_payment_proof"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("installation_requests", sa.Column("payment_qr_code_blob", sa.LargeBinary(length=4294967295), nullable=True))
    op.add_column("installation_requests", sa.Column("payment_qr_code_filename", sa.String(length=255), nullable=True))
    op.add_column("installation_requests", sa.Column("payment_qr_code_content_type", sa.String(length=100), nullable=True))
    op.add_column("installation_requests", sa.Column("payment_qr_code_size_bytes", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("installation_requests", "payment_qr_code_size_bytes")
    op.drop_column("installation_requests", "payment_qr_code_content_type")
    op.drop_column("installation_requests", "payment_qr_code_filename")
    op.drop_column("installation_requests", "payment_qr_code_blob")
