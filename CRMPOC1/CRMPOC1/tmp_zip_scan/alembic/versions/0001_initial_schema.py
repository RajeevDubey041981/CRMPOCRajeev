"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(100), nullable=False, server_default="callcenter"),
        sa.Column("phone", sa.String(20)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("description", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("module", sa.String(100), nullable=False),
        sa.Column("can_view", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("can_create", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("can_edit", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("can_delete", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("can_export", sa.Boolean, nullable=False, server_default=sa.false()),
    )

    op.create_table(
        "item_masters",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("item_code", sa.String(100), nullable=False, unique=True),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_item_masters_item_code", "item_masters", ["item_code"])

    op.create_table(
        "couriers",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("courier_name", sa.String(255), nullable=False),
        sa.Column("contact_name", sa.String(255)),
        sa.Column("contact_mobile", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("address", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )

    op.create_table(
        "vendors",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("vendor_code", sa.String(50), nullable=False, unique=True),
        sa.Column("name_of_firm", sa.String(255), nullable=False),
        sa.Column("contact_name", sa.String(255)),
        sa.Column("contact_mobile", sa.String(20)),
        sa.Column("email", sa.String(255)),
        sa.Column("gst_no", sa.String(20)),
        sa.Column("address", sa.Text),
        sa.Column("state", sa.String(100)),
        sa.Column("district", sa.String(100)),
        sa.Column("pincode", sa.String(10)),
        sa.Column("latitude", sa.Numeric(10, 8)),
        sa.Column("longitude", sa.Numeric(11, 8)),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_vendors_vendor_code", "vendors", ["vendor_code"])

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("order_no", sa.String(255), nullable=False, unique=True),
        sa.Column("order_date", sa.Date, nullable=False),
        sa.Column("oem_bill_no", sa.String(100)),
        sa.Column("vendor_id", sa.Integer, sa.ForeignKey("vendors.id")),
        sa.Column("customer_name", sa.String(255)),
        sa.Column("customer_contact", sa.String(20)),
        sa.Column("customer_email", sa.String(255)),
        sa.Column("customer_city", sa.String(100)),
        sa.Column("courier_id", sa.Integer, sa.ForeignKey("couriers.id")),
        sa.Column("lrn_no", sa.String(100)),
        sa.Column("vendor_bill_no", sa.String(100)),
        sa.Column("vendor_bill_date", sa.Date),
        sa.Column("status", sa.String(50), nullable=False, server_default="Pending"),
        sa.Column("expected_delivery_date", sa.Date),
        sa.Column("actual_delivery_date", sa.Date),
        sa.Column("order_file_path", sa.String(500)),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_vendor", "orders", ["vendor_id"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("order_id", sa.Integer, sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_id", sa.Integer, sa.ForeignKey("item_masters.id")),
        sa.Column("serial_no", sa.String(100)),
        sa.Column("serial_no_2", sa.String(100)),
        sa.Column("pcb_warranty_date", sa.Date),
        sa.Column("component_warranty_date", sa.Date),
        sa.Column("machine_warranty_date", sa.Date),
        sa.Column("free_service_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("service_consume_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("installation_status", sa.String(50), nullable=False, server_default="Not Requested"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_order_items_serial", "order_items", ["serial_no"])

    op.create_table(
        "complaints",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("comp_no", sa.String(100), nullable=False, unique=True),
        sa.Column("comp_date", sa.Date, nullable=False, server_default=sa.func.current_date()),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_mobile", sa.String(20), nullable=False),
        sa.Column("customer_email", sa.String(255)),
        sa.Column("customer_address", sa.Text),
        sa.Column("model_details", sa.String(255)),
        sa.Column("problem_description", sa.Text),
        sa.Column("query_type", sa.String(50)),
        sa.Column("status", sa.String(50), nullable=False, server_default="Pending"),
        sa.Column("status_date", sa.DateTime(timezone=True)),
        sa.Column("assigned_engineer", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("remark", sa.Text),
        sa.Column("service_proof_path", sa.String(500)),
        sa.Column("access_code", sa.String(100)),
        sa.Column("send_sms", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("source", sa.String(50), nullable=False, server_default="callcenter"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("idx_complaints_status", "complaints", ["status"])
    op.create_index("idx_complaints_mobile", "complaints", ["customer_mobile"])
    op.create_index("idx_complaints_comp_no", "complaints", ["comp_no"])
    op.create_index("idx_complaints_engineer", "complaints", ["assigned_engineer"])

    op.create_table(
        "complaint_status_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("complaint_id", sa.Integer, sa.ForeignKey("complaints.id"), nullable=False),
        sa.Column("old_status", sa.String(50)),
        sa.Column("new_status", sa.String(50)),
        sa.Column("changed_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("remark", sa.Text),
        sa.Column("document_path", sa.String(500)),
        sa.Column("action_taken", sa.String(100)),
        sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "installation_requests",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("contact_number", sa.String(20), nullable=False),
        sa.Column("address", sa.Text),
        sa.Column("order_item_id", sa.Integer, sa.ForeignKey("order_items.id")),
        sa.Column("product_name", sa.String(255)),
        sa.Column("request_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("assigned_engineer", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("status", sa.String(50), nullable=False, server_default="Pending"),
        sa.Column("installation_date", sa.DateTime(timezone=True)),
        sa.Column("work_report", sa.Text),
        sa.Column("work_report_file_path", sa.String(500)),
        sa.Column("settlement_approved_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_installations_status", "installation_requests", ["status"])
    op.create_index("idx_installations_date", "installation_requests", ["request_date"])

    op.create_table(
        "calls",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("ref_no", sa.String(100), nullable=False, unique=True),
        sa.Column("customer_name", sa.String(255)),
        sa.Column("customer_email", sa.String(255)),
        sa.Column("phone", sa.String(20)),
        sa.Column("call_type", sa.String(20)),
        sa.Column("status", sa.String(30)),
        sa.Column("assigned_to", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("duration_secs", sa.Integer),
        sa.Column("call_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("followup_date", sa.DateTime(timezone=True)),
        sa.Column("notes", sa.Text),
        sa.Column("complaint_id", sa.Integer, sa.ForeignKey("complaints.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_calls_status", "calls", ["status"])
    op.create_index("idx_calls_followup", "calls", ["followup_date"])

    op.create_table(
        "claims",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("claim_id", sa.String(100), nullable=False, unique=True),
        sa.Column("order_no", sa.String(255)),
        sa.Column("serial_number", sa.String(100)),
        sa.Column("order_item_id", sa.Integer, sa.ForeignKey("order_items.id")),
        sa.Column("customer_name", sa.String(255)),
        sa.Column("customer_contact", sa.String(20)),
        sa.Column("customer_email", sa.String(255)),
        sa.Column("status", sa.String(50), nullable=False, server_default="Processing"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_by", sa.Integer, sa.ForeignKey("users.id")),
        sa.Column("notes", sa.Text),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "claim_photos",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("claim_id", sa.Integer, sa.ForeignKey("claims.id", ondelete="CASCADE"), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("claim_photos")
    op.drop_table("claims")
    op.drop_index("idx_calls_followup", table_name="calls")
    op.drop_index("idx_calls_status", table_name="calls")
    op.drop_table("calls")
    op.drop_index("idx_installations_date", table_name="installation_requests")
    op.drop_index("idx_installations_status", table_name="installation_requests")
    op.drop_table("installation_requests")
    op.drop_table("complaint_status_logs")
    op.drop_index("idx_complaints_engineer", table_name="complaints")
    op.drop_index("idx_complaints_comp_no", table_name="complaints")
    op.drop_index("idx_complaints_mobile", table_name="complaints")
    op.drop_index("idx_complaints_status", table_name="complaints")
    op.drop_table("complaints")
    op.drop_index("idx_order_items_serial", table_name="order_items")
    op.drop_table("order_items")
    op.drop_index("idx_orders_vendor", table_name="orders")
    op.drop_index("idx_orders_status", table_name="orders")
    op.drop_table("orders")
    op.drop_index("ix_vendors_vendor_code", table_name="vendors")
    op.drop_table("vendors")
    op.drop_table("couriers")
    op.drop_index("ix_item_masters_item_code", table_name="item_masters")
    op.drop_table("item_masters")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
