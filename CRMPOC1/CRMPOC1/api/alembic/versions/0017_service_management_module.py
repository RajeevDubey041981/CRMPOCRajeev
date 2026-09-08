"""service management module

Revision ID: 0017_service_management_module
Revises: 0016_payment_transactions
Create Date: 2026-08-17 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0017_service_management_module"
down_revision = "0016_payment_transactions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "service_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("request_no", sa.String(length=100), nullable=False),
        sa.Column("request_date", sa.Date(), nullable=False),
        sa.Column("query_type", sa.String(length=50), nullable=False),
        sa.Column("customer_name", sa.String(length=255), nullable=False),
        sa.Column("customer_mobile", sa.String(length=20), nullable=False),
        sa.Column("customer_email", sa.String(length=255), nullable=True),
        sa.Column("customer_address", sa.Text(), nullable=True),
        sa.Column("model_details", sa.String(length=255), nullable=True),
        sa.Column("problem_description", sa.Text(), nullable=True),
        sa.Column("additional_remarks", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("status_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("order_item_id", sa.Integer(), nullable=True),
        sa.Column("serial_no", sa.String(length=100), nullable=True),
        sa.Column("service_type", sa.String(length=50), nullable=True),
        sa.Column("warranty_status", sa.String(length=50), nullable=True),
        sa.Column("assigned_engineer_id", sa.Integer(), nullable=True),
        sa.Column("assigned_vendor_id", sa.Integer(), nullable=True),
        sa.Column("requires_documents", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ask_for_documents", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("document_request_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("document_access_token", sa.String(length=120), nullable=True),
        sa.Column("customer_identified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["assigned_engineer_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assigned_vendor_id"], ["vendors.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["order_item_id"], ["order_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_requests_request_no"), "service_requests", ["request_no"], unique=True)
    op.create_index(op.f("ix_service_requests_customer_mobile"), "service_requests", ["customer_mobile"], unique=False)
    op.create_index(op.f("ix_service_requests_status"), "service_requests", ["status"], unique=False)
    op.create_index(op.f("ix_service_requests_order_id"), "service_requests", ["order_id"], unique=False)
    op.create_index(op.f("ix_service_requests_order_item_id"), "service_requests", ["order_item_id"], unique=False)
    op.create_index(op.f("ix_service_requests_serial_no"), "service_requests", ["serial_no"], unique=False)
    op.create_index(op.f("ix_service_requests_service_type"), "service_requests", ["service_type"], unique=False)
    op.create_index(op.f("ix_service_requests_assigned_engineer_id"), "service_requests", ["assigned_engineer_id"], unique=False)
    op.create_index(op.f("ix_service_requests_assigned_vendor_id"), "service_requests", ["assigned_vendor_id"], unique=False)
    op.create_index(op.f("ix_service_requests_document_access_token"), "service_requests", ["document_access_token"], unique=False)

    op.create_table(
        "service_status_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("old_status", sa.String(length=50), nullable=True),
        sa.Column("new_status", sa.String(length=50), nullable=True),
        sa.Column("performed_by", sa.Integer(), nullable=True),
        sa.Column("performed_role", sa.String(length=100), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["performed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_status_logs_service_request_id"), "service_status_logs", ["service_request_id"], unique=False)

    op.create_table(
        "service_assignments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("assignee_type", sa.String(length=20), nullable=False),
        sa.Column("assignee_user_id", sa.Integer(), nullable=True),
        sa.Column("assignee_vendor_id", sa.Integer(), nullable=True),
        sa.Column("assigned_by", sa.Integer(), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.ForeignKeyConstraint(["assigned_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["assignee_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["assignee_vendor_id"], ["vendors.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_assignments_service_request_id"), "service_assignments", ["service_request_id"], unique=False)
    op.create_index(op.f("ix_service_assignments_assignee_user_id"), "service_assignments", ["assignee_user_id"], unique=False)
    op.create_index(op.f("ix_service_assignments_assignee_vendor_id"), "service_assignments", ["assignee_vendor_id"], unique=False)

    op.create_table(
        "service_observations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("submitted_by_user_id", sa.Integer(), nullable=True),
        sa.Column("serial_no", sa.String(length=100), nullable=True),
        sa.Column("warranty_status", sa.String(length=50), nullable=True),
        sa.Column("service_type", sa.String(length=50), nullable=True),
        sa.Column("problem_found", sa.Text(), nullable=True),
        sa.Column("observation", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("parts_required_json", sa.Text(), nullable=True),
        sa.Column("estimated_service_charge", sa.Numeric(12, 2), nullable=True),
        sa.Column("estimated_parts_charge", sa.Numeric(12, 2), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.ForeignKeyConstraint(["submitted_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_observations_service_request_id"), "service_observations", ["service_request_id"], unique=False)

    op.create_table(
        "service_approvals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("observation_id", sa.Integer(), nullable=True),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("approved_by", sa.Integer(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["approved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["observation_id"], ["service_observations.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_approvals_service_request_id"), "service_approvals", ["service_request_id"], unique=False)

    op.create_table(
        "service_completions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("performed_by_type", sa.String(length=20), nullable=False),
        sa.Column("performed_by_user_id", sa.Integer(), nullable=True),
        sa.Column("performed_by_vendor_id", sa.Integer(), nullable=True),
        sa.Column("work_performed", sa.Text(), nullable=True),
        sa.Column("parts_replaced_json", sa.Text(), nullable=True),
        sa.Column("service_notes", sa.Text(), nullable=True),
        sa.Column("service_date", sa.Date(), nullable=True),
        sa.Column("before_photos_json", sa.Text(), nullable=True),
        sa.Column("after_photos_json", sa.Text(), nullable=True),
        sa.Column("customer_acknowledgement_path", sa.String(length=500), nullable=True),
        sa.Column("final_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("completion_remarks", sa.Text(), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["performed_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["performed_by_vendor_id"], ["vendors.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_completions_service_request_id"), "service_completions", ["service_request_id"], unique=False)

    op.create_table(
        "service_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("uploaded_by_type", sa.String(length=50), nullable=False),
        sa.Column("uploaded_by_user_id", sa.Integer(), nullable=True),
        sa.Column("uploaded_by_customer_name", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("reviewed_by", sa.Integer(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_remarks", sa.Text(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.ForeignKeyConstraint(["uploaded_by_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_documents_service_request_id"), "service_documents", ["service_request_id"], unique=False)

    op.create_table(
        "service_document_rules",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_type", sa.String(length=50), nullable=True),
        sa.Column("warranty_status", sa.String(length=50), nullable=True),
        sa.Column("query_type", sa.String(length=50), nullable=True),
        sa.Column("document_type", sa.String(length=100), nullable=False),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "service_payment_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("service_request_id", sa.Integer(), nullable=False),
        sa.Column("requested_by_type", sa.String(length=20), nullable=False),
        sa.Column("requested_by_user_id", sa.Integer(), nullable=True),
        sa.Column("requested_by_vendor_id", sa.Integer(), nullable=True),
        sa.Column("service_type", sa.String(length=50), nullable=True),
        sa.Column("customer_charge_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("settlement_service_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("settlement_parts_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("total_requested_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("payment_type", sa.String(length=50), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["requested_by_vendor_id"], ["vendors.id"]),
        sa.ForeignKeyConstraint(["service_request_id"], ["service_requests.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_service_payment_requests_service_request_id"), "service_payment_requests", ["service_request_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_service_payment_requests_service_request_id"), table_name="service_payment_requests")
    op.drop_table("service_payment_requests")
    op.drop_table("service_document_rules")
    op.drop_index(op.f("ix_service_documents_service_request_id"), table_name="service_documents")
    op.drop_table("service_documents")
    op.drop_index(op.f("ix_service_completions_service_request_id"), table_name="service_completions")
    op.drop_table("service_completions")
    op.drop_index(op.f("ix_service_approvals_service_request_id"), table_name="service_approvals")
    op.drop_table("service_approvals")
    op.drop_index(op.f("ix_service_observations_service_request_id"), table_name="service_observations")
    op.drop_table("service_observations")
    op.drop_index(op.f("ix_service_assignments_assignee_vendor_id"), table_name="service_assignments")
    op.drop_index(op.f("ix_service_assignments_assignee_user_id"), table_name="service_assignments")
    op.drop_index(op.f("ix_service_assignments_service_request_id"), table_name="service_assignments")
    op.drop_table("service_assignments")
    op.drop_index(op.f("ix_service_status_logs_service_request_id"), table_name="service_status_logs")
    op.drop_table("service_status_logs")
    op.drop_index(op.f("ix_service_requests_document_access_token"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_assigned_vendor_id"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_assigned_engineer_id"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_service_type"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_serial_no"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_order_item_id"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_order_id"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_status"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_customer_mobile"), table_name="service_requests")
    op.drop_index(op.f("ix_service_requests_request_no"), table_name="service_requests")
    op.drop_table("service_requests")
