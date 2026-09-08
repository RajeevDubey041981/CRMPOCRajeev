"""Call center installation request workflow.

Revision ID: 0028_installation_callcenter_flow
Revises: 0027_complaint_order_id
Create Date: 2026-08-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0028_installation_callcenter_flow"
down_revision: Union[str, None] = "0027_complaint_order_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("installation_requests", sa.Column("source", sa.String(length=50), nullable=False, server_default="vendor"))
    op.add_column("installation_requests", sa.Column("order_id", sa.Integer(), nullable=True))
    op.add_column("installation_requests", sa.Column("created_by", sa.Integer(), nullable=True))
    op.add_column("installation_requests", sa.Column("document_access_token", sa.String(length=120), nullable=True))
    op.add_column("installation_requests", sa.Column("ask_for_documents", sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column("installation_requests", sa.Column("document_request_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("installation_requests", sa.Column("order_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("installation_requests", sa.Column("order_verified_by", sa.Integer(), nullable=True))
    op.add_column("installation_requests", sa.Column("engineer_entered_serial_no", sa.String(length=100), nullable=True))
    op.add_column("installation_requests", sa.Column("engineer_entered_serial_no_2", sa.String(length=100), nullable=True))
    op.add_column("installation_requests", sa.Column("serial_verified_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("installation_requests", sa.Column("serial_verified_by", sa.Integer(), nullable=True))
    op.add_column("installation_requests", sa.Column("admin_billing_type", sa.String(length=20), nullable=True))
    op.add_column("installation_requests", sa.Column("admin_approval_remark", sa.Text(), nullable=True))
    op.add_column("installation_requests", sa.Column("admin_approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("installation_requests", sa.Column("admin_approved_by", sa.Integer(), nullable=True))
    op.add_column("installation_requests", sa.Column("customer_email", sa.String(length=255), nullable=True))

    op.create_foreign_key("fk_installation_requests_order_id_orders", "installation_requests", "orders", ["order_id"], ["id"])
    op.create_foreign_key("fk_installation_requests_created_by_users", "installation_requests", "users", ["created_by"], ["id"])
    op.create_foreign_key("fk_installation_requests_order_verified_by_users", "installation_requests", "users", ["order_verified_by"], ["id"])
    op.create_foreign_key("fk_installation_requests_serial_verified_by_users", "installation_requests", "users", ["serial_verified_by"], ["id"])
    op.create_foreign_key("fk_installation_requests_admin_approved_by_users", "installation_requests", "users", ["admin_approved_by"], ["id"])
    op.create_index("ix_installation_requests_order_id", "installation_requests", ["order_id"])
    op.create_index("ix_installation_requests_source", "installation_requests", ["source"])
    op.create_index("ix_installation_requests_document_access_token", "installation_requests", ["document_access_token"])

    op.create_table(
        "installation_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("installation_request_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("uploaded_by_type", sa.String(length=50), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_by_customer_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="Uploaded"),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_remarks", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["installation_request_id"], ["installation_requests.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_installation_documents_installation_request_id", "installation_documents", ["installation_request_id"])

    op.create_table(
        "installation_status_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("installation_request_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("old_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=True),
        sa.Column("performed_by", sa.Integer(), nullable=True),
        sa.Column("performed_role", sa.String(length=100), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["installation_request_id"], ["installation_requests.id"]),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_installation_status_logs_installation_request_id", "installation_status_logs", ["installation_request_id"])

    op.execute(
        """
        UPDATE installation_requests ir
        INNER JOIN order_items oi ON ir.order_item_id = oi.id
        SET ir.order_id = oi.order_id
        WHERE ir.order_id IS NULL AND ir.order_item_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_installation_status_logs_installation_request_id", table_name="installation_status_logs")
    op.drop_table("installation_status_logs")
    op.drop_index("ix_installation_documents_installation_request_id", table_name="installation_documents")
    op.drop_table("installation_documents")
    op.drop_index("ix_installation_requests_document_access_token", table_name="installation_requests")
    op.drop_index("ix_installation_requests_source", table_name="installation_requests")
    op.drop_index("ix_installation_requests_order_id", table_name="installation_requests")
    op.drop_constraint("fk_installation_requests_admin_approved_by_users", "installation_requests", type_="foreignkey")
    op.drop_constraint("fk_installation_requests_serial_verified_by_users", "installation_requests", type_="foreignkey")
    op.drop_constraint("fk_installation_requests_order_verified_by_users", "installation_requests", type_="foreignkey")
    op.drop_constraint("fk_installation_requests_created_by_users", "installation_requests", type_="foreignkey")
    op.drop_constraint("fk_installation_requests_order_id_orders", "installation_requests", type_="foreignkey")
    for col in (
        "customer_email", "admin_approved_by", "admin_approved_at", "admin_approval_remark",
        "admin_billing_type", "serial_verified_by", "serial_verified_at",
        "engineer_entered_serial_no_2", "engineer_entered_serial_no",
        "order_verified_by", "order_verified_at", "document_request_sent_at",
        "ask_for_documents", "document_access_token", "created_by", "order_id", "source",
    ):
        op.drop_column("installation_requests", col)
