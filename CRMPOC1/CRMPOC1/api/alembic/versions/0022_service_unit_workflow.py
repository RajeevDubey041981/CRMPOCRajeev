"""Per-unit serial verification and observations

Revision ID: 0022_service_unit_workflow
Revises: 0021_service_unit_assignment
Create Date: 2026-08-23
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022_service_unit_workflow"
down_revision: Union[str, None] = "0021_service_unit_assignment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "service_request_units",
        sa.Column("serial_verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "service_request_units",
        sa.Column("warranty_status", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "service_request_units",
        sa.Column("service_type", sa.String(length=50), nullable=True),
    )
    op.add_column(
        "service_observations",
        sa.Column("service_request_unit_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_service_observations_service_request_unit_id",
        "service_observations",
        ["service_request_unit_id"],
    )
    op.create_foreign_key(
        "service_observations_service_request_unit_id_fkey",
        "service_observations",
        "service_request_units",
        ["service_request_unit_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "service_observations_service_request_unit_id_fkey",
        "service_observations",
        type_="foreignkey",
    )
    op.drop_index("ix_service_observations_service_request_unit_id", table_name="service_observations")
    op.drop_column("service_observations", "service_request_unit_id")
    op.drop_column("service_request_units", "service_type")
    op.drop_column("service_request_units", "warranty_status")
    op.drop_column("service_request_units", "serial_verified_at")
