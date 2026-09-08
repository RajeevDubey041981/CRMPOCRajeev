"""link service requests to complaints

Revision ID: 0019_link_service_requests_to_complaints
Revises: 0018_service_notifications_and_payment_completion
Create Date: 2026-08-19 18:30:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0019_link_service_requests_to_complaints"
down_revision = "0018_service_notifications_and_payment_completion"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("service_requests", sa.Column("complaint_id", sa.Integer(), nullable=True))
    op.create_index(op.f("ix_service_requests_complaint_id"), "service_requests", ["complaint_id"], unique=False)
    op.create_foreign_key(None, "service_requests", "complaints", ["complaint_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint(None, "service_requests", type_="foreignkey")
    op.drop_index(op.f("ix_service_requests_complaint_id"), table_name="service_requests")
    op.drop_column("service_requests", "complaint_id")
