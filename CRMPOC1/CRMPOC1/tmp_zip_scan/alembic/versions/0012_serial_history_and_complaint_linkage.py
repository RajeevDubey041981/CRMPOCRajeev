"""Add serial history events table and complaint serial linkage.

Revision ID: 0012_serial_history_and_complaint_linkage
Revises: 0011_order_search_indexes
Create Date: 2026-08-04
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0012_serial_history_and_complaint_linkage"
down_revision: Union[str, None] = "0011_order_search_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("complaints", sa.Column("order_item_id", sa.Integer(), nullable=True))
    op.add_column("complaints", sa.Column("serial_no", sa.String(length=100), nullable=True))
    op.create_index(op.f("ix_complaints_order_item_id"), "complaints", ["order_item_id"], unique=False)
    op.create_index(op.f("ix_complaints_serial_no"), "complaints", ["serial_no"], unique=False)
    op.create_foreign_key(
        "fk_complaints_order_item_id_order_items",
        "complaints",
        "order_items",
        ["order_item_id"],
        ["id"],
    )

    op.create_table(
        "serial_history_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_item_id", sa.Integer(), nullable=True),
        sa.Column("serial_no", sa.String(length=100), nullable=False),
        sa.Column("serial_no_2", sa.String(length=100), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("event_subtype", sa.String(length=100), nullable=True),
        sa.Column("event_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("performed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("performed_by_name", sa.String(length=255), nullable=True),
        sa.Column("source_table", sa.String(length=100), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["order_item_id"], ["order_items.id"]),
        sa.ForeignKeyConstraint(["performed_by_user_id"], ["users.id"]),
        sa.UniqueConstraint("source_table", "source_id", "event_type", "serial_no", name="uq_serial_history_source_event"),
    )
    op.create_index(op.f("ix_serial_history_events_serial_no"), "serial_history_events", ["serial_no"], unique=False)
    op.create_index(op.f("ix_serial_history_events_order_item_id"), "serial_history_events", ["order_item_id"], unique=False)
    op.create_index(op.f("ix_serial_history_events_event_at"), "serial_history_events", ["event_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_serial_history_events_event_at"), table_name="serial_history_events")
    op.drop_index(op.f("ix_serial_history_events_order_item_id"), table_name="serial_history_events")
    op.drop_index(op.f("ix_serial_history_events_serial_no"), table_name="serial_history_events")
    op.drop_table("serial_history_events")
    op.drop_constraint("fk_complaints_order_item_id_order_items", "complaints", type_="foreignkey")
    op.drop_index(op.f("ix_complaints_serial_no"), table_name="complaints")
    op.drop_index(op.f("ix_complaints_order_item_id"), table_name="complaints")
    op.drop_column("complaints", "serial_no")
    op.drop_column("complaints", "order_item_id")
