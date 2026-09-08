"""Add partner email resend tracking and cancellation status.

Revision ID: 0036_partner_registration_email_controls
Revises: 0035_partner_registration_public_flow
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "0036_partner_registration_email_controls"
down_revision: Union[str, None] = "0035_partner_registration_public_flow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "partner_registrations",
        sa.Column("email_resend_used", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("partner_registrations", "email_resend_used")