"""Partner registration public invite flow with progress tracking.

Revision ID: 0035_partner_registration_public_flow
Revises: 0034_partner_registration_form_fields
Create Date: 2026-09-05
"""

import secrets
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0035_partner_registration_public_flow"
down_revision: Union[str, None] = "0034_partner_registration_form_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("partner_registrations", sa.Column("access_token", sa.String(length=64), nullable=True))
    op.add_column(
        "partner_registrations",
        sa.Column("form_status", sa.String(length=30), nullable=False, server_default="Submitted"),
    )
    op.add_column(
        "partner_registrations",
        sa.Column("current_form_step", sa.Integer(), nullable=False, server_default="8"),
    )
    op.add_column(
        "partner_registrations",
        sa.Column("completion_percent", sa.Integer(), nullable=False, server_default="100"),
    )
    op.add_column("partner_registrations", sa.Column("invited_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("partner_registrations", sa.Column("form_started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("partner_registrations", sa.Column("form_submitted_at", sa.DateTime(timezone=True), nullable=True))

    op.alter_column("partner_registrations", "name", existing_type=sa.String(length=255), nullable=True)
    op.alter_column("partner_registrations", "mobile", existing_type=sa.String(length=20), nullable=True)
    op.alter_column("partner_registrations", "contact_person_name", existing_type=sa.String(length=255), nullable=True)

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id FROM partner_registrations WHERE access_token IS NULL")).fetchall()
    for row in rows:
        conn.execute(
            sa.text("UPDATE partner_registrations SET access_token = :token WHERE id = :id"),
            {"token": secrets.token_urlsafe(32), "id": row.id},
        )

    op.alter_column("partner_registrations", "access_token", existing_type=sa.String(length=64), nullable=False)
    op.create_index("ix_partner_registrations_access_token", "partner_registrations", ["access_token"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_partner_registrations_access_token", table_name="partner_registrations")
    op.alter_column("partner_registrations", "contact_person_name", existing_type=sa.String(length=255), nullable=False)
    op.alter_column("partner_registrations", "mobile", existing_type=sa.String(length=20), nullable=False)
    op.alter_column("partner_registrations", "name", existing_type=sa.String(length=255), nullable=False)
    op.drop_column("partner_registrations", "form_submitted_at")
    op.drop_column("partner_registrations", "form_started_at")
    op.drop_column("partner_registrations", "invited_at")
    op.drop_column("partner_registrations", "completion_percent")
    op.drop_column("partner_registrations", "current_form_step")
    op.drop_column("partner_registrations", "form_status")
    op.drop_column("partner_registrations", "access_token")
