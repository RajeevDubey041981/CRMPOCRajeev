"""service notifications and payment completion

Revision ID: 0018_service_notifications_and_payment_completion
Revises: 0017_service_management_module
Create Date: 2026-08-17 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0018_service_notifications_and_payment_completion"
down_revision = "0017_service_management_module"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("service_status_logs", sa.Column("serial_history_source_id", sa.Integer(), nullable=True))
    op.add_column("service_completions", sa.Column("old_part_serial_no", sa.String(length=100), nullable=True))
    op.add_column("service_completions", sa.Column("new_part_serial_no", sa.String(length=100), nullable=True))
    op.add_column("service_payment_requests", sa.Column("processed_by_user_id", sa.Integer(), nullable=True))
    op.add_column("service_payment_requests", sa.Column("payment_transaction_id", sa.Integer(), nullable=True))
    op.create_foreign_key(None, "service_payment_requests", "users", ["processed_by_user_id"], ["id"])
    op.create_foreign_key(None, "service_payment_requests", "payment_transactions", ["payment_transaction_id"], ["id"])
    op.create_table(
        "service_notifications",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("recipient_user_id", sa.Integer(), nullable=True),
        sa.Column("recipient_vendor_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["recipient_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["recipient_vendor_id"], ["vendors.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_notifications_service_request_id"), "service_notifications", ["service_request_id"], unique=False)
    op.create_index(op.f("ix_service_notifications_recipient_user_id"), "service_notifications", ["recipient_user_id"], unique=False)
    op.create_index(op.f("ix_service_notifications_recipient_vendor_id"), "service_notifications", ["recipient_vendor_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_service_notifications_recipient_vendor_id"), table_name="service_notifications")
    op.drop_index(op.f("ix_service_notifications_recipient_user_id"), table_name="service_notifications")
    op.drop_index(op.f("ix_service_notifications_service_request_id"), table_name="service_notifications")
    op.drop_table("service_notifications")
    op.drop_constraint(None, "service_payment_requests", type_="foreignkey")
    op.drop_constraint(None, "service_payment_requests", type_="foreignkey")
    op.drop_column("service_payment_requests", "payment_transaction_id")
    op.drop_column("service_payment_requests", "processed_by_user_id")
    op.drop_column("service_completions", "new_part_serial_no")
    op.drop_column("service_completions", "old_part_serial_no")
    op.drop_column("service_status_logs", "serial_history_source_id")
