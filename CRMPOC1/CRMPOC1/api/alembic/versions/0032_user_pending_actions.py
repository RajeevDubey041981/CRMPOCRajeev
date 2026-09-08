"""Add user_pending_actions table for cross-module pending work notifications.

Revision ID: 0032_user_pending_actions
Revises: 0031_installation_split_and_completion
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0032_user_pending_actions"
down_revision: Union[str, None] = "0031_installation_split_and_completion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_pending_actions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=False),
        sa.Column("recipient_vendor_id", sa.Integer(), nullable=True),
        sa.Column("module", sa.String(length=30), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("entity_ref", sa.String(length=80), nullable=False, server_default=""),
        sa.Column("action_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("action_label", sa.String(length=120), nullable=False),
        sa.Column("href", sa.String(length=500), nullable=False),
        sa.Column("entity_status", sa.String(length=50), nullable=False, server_default=""),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["recipient_vendor_id"], ["vendors.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "recipient_user_id",
            "module",
            "entity_id",
            "entity_ref",
            "action_type",
            name="uq_user_pending_actions_recipient_entity_action",
        ),
    )
    op.create_index("ix_user_pending_actions_recipient_active", "user_pending_actions", ["recipient_user_id", "is_active"])
    op.create_index("ix_user_pending_actions_module_entity", "user_pending_actions", ["module", "entity_id"])


def downgrade() -> None:
    op.drop_index("ix_user_pending_actions_module_entity", table_name="user_pending_actions")
    op.drop_index("ix_user_pending_actions_recipient_active", table_name="user_pending_actions")
    op.drop_table("user_pending_actions")
