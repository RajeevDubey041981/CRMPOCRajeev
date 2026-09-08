"""Add partner_registrations table for GeM partner onboarding.

Revision ID: 0033_partner_registrations
Revises: 0032_user_pending_actions
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0033_partner_registrations"
down_revision: Union[str, None] = "0032_user_pending_actions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "partner_registrations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("registration_no", sa.String(length=50), nullable=False),
        sa.Column("partner_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("mobile", sa.String(length=20), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("contact_person_name", sa.String(length=255), nullable=False),
        sa.Column("onboarding_status", sa.String(length=50), nullable=False, server_default="Registration Submitted"),
        sa.Column("firm_address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("pincode", sa.String(length=20), nullable=True),
        sa.Column("gst_no", sa.String(length=20), nullable=True),
        sa.Column("pan_no", sa.String(length=20), nullable=True),
        sa.Column("gem_seller_id", sa.String(length=100), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("admin_remark", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("status_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("registration_no"),
    )
    op.create_index("ix_partner_registrations_partner_type", "partner_registrations", ["partner_type"])
    op.create_index("ix_partner_registrations_onboarding_status", "partner_registrations", ["onboarding_status"])
    op.create_index("ix_partner_registrations_mobile", "partner_registrations", ["mobile"])
    op.create_index("ix_partner_registrations_email", "partner_registrations", ["email"])


def downgrade() -> None:
    op.drop_index("ix_partner_registrations_email", table_name="partner_registrations")
    op.drop_index("ix_partner_registrations_mobile", table_name="partner_registrations")
    op.drop_index("ix_partner_registrations_onboarding_status", table_name="partner_registrations")
    op.drop_index("ix_partner_registrations_partner_type", table_name="partner_registrations")
    op.drop_table("partner_registrations")
