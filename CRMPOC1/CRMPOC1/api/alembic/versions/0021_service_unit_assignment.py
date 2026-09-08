"""Service request unit-level assignment tables

Revision ID: 0021_service_unit_assignment
Revises: 0020_item_master_serial_count
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021_service_unit_assignment"
down_revision: Union[str, None] = "0020_item_master_serial_count"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "service_request_items",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("item_code", sa.String(length=100), nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=True),
        sa.Column("item_name", sa.String(length=255), nullable=True),
        sa.Column("ordered_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("serial_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["item_masters.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_request_items_service_request_id", "service_request_items", ["service_request_id"])
    op.create_index("ix_service_request_items_order_id", "service_request_items", ["order_id"])
    op.create_index("ix_service_request_items_item_code", "service_request_items", ["item_code"])

    op.create_table(
        "service_request_units",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("service_request_item_id", sa.Integer(), nullable=False),
        sa.Column("order_item_id", sa.Integer(), nullable=False),
        sa.Column("serial_no", sa.String(length=100), nullable=True),
        sa.Column("serial_no_2", sa.String(length=100), nullable=True),
        sa.Column("assigned_engineer_id", sa.Integer(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_engineer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_item_id"], ["order_items.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.ForeignKeyConstraint(["service_request_item_id"], ["service_request_items.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("service_request_id", "order_item_id", name="uq_service_request_units_sr_order_item"),
    )
    op.create_index("ix_service_request_units_service_request_id", "service_request_units", ["service_request_id"])
    op.create_index("ix_service_request_units_service_request_item_id", "service_request_units", ["service_request_item_id"])
    op.create_index("ix_service_request_units_order_item_id", "service_request_units", ["order_item_id"])
    op.create_index("ix_service_request_units_assigned_engineer_id", "service_request_units", ["assigned_engineer_id"])

    op.create_table(
        "service_unit_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("service_request_unit_id", sa.Integer(), nullable=False),
        sa.Column("engineer_id", sa.Integer(), nullable=False),
        sa.Column("assigned_by_user_id", sa.Integer(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("unassigned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["assigned_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["engineer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.ForeignKeyConstraint(["service_request_unit_id"], ["service_request_units.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_unit_assignments_service_request_id", "service_unit_assignments", ["service_request_id"])
    op.create_index("ix_service_unit_assignments_service_request_unit_id", "service_unit_assignments", ["service_request_unit_id"])
    op.create_index("ix_service_unit_assignments_engineer_id", "service_unit_assignments", ["engineer_id"])


def downgrade() -> None:
    op.drop_index("ix_service_unit_assignments_engineer_id", table_name="service_unit_assignments")
    op.drop_index("ix_service_unit_assignments_service_request_unit_id", table_name="service_unit_assignments")
    op.drop_index("ix_service_unit_assignments_service_request_id", table_name="service_unit_assignments")
    op.drop_table("service_unit_assignments")
    op.drop_index("ix_service_request_units_assigned_engineer_id", table_name="service_request_units")
    op.drop_index("ix_service_request_units_order_item_id", table_name="service_request_units")
    op.drop_index("ix_service_request_units_service_request_item_id", table_name="service_request_units")
    op.drop_index("ix_service_request_units_service_request_id", table_name="service_request_units")
    op.drop_table("service_request_units")
    op.drop_index("ix_service_request_items_item_code", table_name="service_request_items")
    op.drop_index("ix_service_request_items_order_id", table_name="service_request_items")
    op.drop_index("ix_service_request_items_service_request_id", table_name="service_request_items")
    op.drop_table("service_request_items")
