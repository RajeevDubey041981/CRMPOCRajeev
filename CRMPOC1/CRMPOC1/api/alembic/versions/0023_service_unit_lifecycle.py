"""Per-unit lifecycle through completion and payment

Revision ID: 0023_service_unit_lifecycle
Revises: 0022_service_unit_workflow
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023_service_unit_lifecycle"
down_revision: Union[str, None] = "0022_service_unit_workflow"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_request_units",
        sa.Column("unit_status", sa.String(length=50), nullable=False, server_default="Assigned"),
    )
    op.add_column(
        "service_approvals",
        sa.Column("service_request_unit_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_service_approvals_service_request_unit_id",
        "service_approvals",
        ["service_request_unit_id"],
    )
    op.create_foreign_key(
        "service_approvals_service_request_unit_id_fkey",
        "service_approvals",
        "service_request_units",
        ["service_request_unit_id"],
        ["id"],
    )
    op.add_column(
        "service_completions",
        sa.Column("service_request_unit_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_service_completions_service_request_unit_id",
        "service_completions",
        ["service_request_unit_id"],
    )
    op.create_foreign_key(
        "service_completions_service_request_unit_id_fkey",
        "service_completions",
        "service_request_units",
        ["service_request_unit_id"],
        ["id"],
    )
    op.add_column(
        "service_payment_requests",
        sa.Column("service_request_unit_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_service_payment_requests_service_request_unit_id",
        "service_payment_requests",
        ["service_request_unit_id"],
    )
    op.create_foreign_key(
        "service_payment_requests_service_request_unit_id_fkey",
        "service_payment_requests",
        "service_request_units",
        ["service_request_unit_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "service_payment_requests_service_request_unit_id_fkey",
        "service_payment_requests",
        type_="foreignkey",
    )
    op.drop_index("ix_service_payment_requests_service_request_unit_id", table_name="service_payment_requests")
    op.drop_column("service_payment_requests", "service_request_unit_id")
    op.drop_constraint(
        "service_completions_service_request_unit_id_fkey",
        "service_completions",
        type_="foreignkey",
    )
    op.drop_index("ix_service_completions_service_request_unit_id", table_name="service_completions")
    op.drop_column("service_completions", "service_request_unit_id")
    op.drop_constraint(
        "service_approvals_service_request_unit_id_fkey",
        "service_approvals",
        type_="foreignkey",
    )
    op.drop_index("ix_service_approvals_service_request_unit_id", table_name="service_approvals")
    op.drop_column("service_approvals", "service_request_unit_id")
    op.drop_column("service_request_units", "unit_status")
