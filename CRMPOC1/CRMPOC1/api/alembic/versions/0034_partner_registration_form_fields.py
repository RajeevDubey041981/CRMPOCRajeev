"""Extend partner_registrations with full registration form fields and documents.

Revision ID: 0034_partner_registration_form_fields
Revises: 0033_partner_registrations
Create Date: 2026-09-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0034_partner_registration_form_fields"
down_revision: Union[str, None] = "0033_partner_registrations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("partner_registrations", sa.Column("business_type", sa.String(length=50), nullable=True))
    op.add_column("partner_registrations", sa.Column("contact_designation", sa.String(length=100), nullable=True))
    op.add_column("partner_registrations", sa.Column("alternate_mobile", sa.String(length=20), nullable=True))
    op.add_column("partner_registrations", sa.Column("district", sa.String(length=100), nullable=True))
    op.add_column("partner_registrations", sa.Column("website", sa.String(length=255), nullable=True))
    op.add_column("partner_registrations", sa.Column("udyam_no", sa.String(length=50), nullable=True))
    op.add_column("partner_registrations", sa.Column("cin_no", sa.String(length=30), nullable=True))
    op.add_column("partner_registrations", sa.Column("aadhaar_no", sa.String(length=20), nullable=True))
    op.add_column("partner_registrations", sa.Column("year_of_establishment", sa.Integer(), nullable=True))
    op.add_column("partner_registrations", sa.Column("annual_turnover", sa.Numeric(14, 2), nullable=True))
    op.add_column("partner_registrations", sa.Column("operating_states", sa.Text(), nullable=True))
    op.add_column("partner_registrations", sa.Column("product_categories", sa.Text(), nullable=True))
    op.add_column("partner_registrations", sa.Column("bank_name", sa.String(length=150), nullable=True))
    op.add_column("partner_registrations", sa.Column("bank_branch", sa.String(length=150), nullable=True))
    op.add_column("partner_registrations", sa.Column("account_holder_name", sa.String(length=255), nullable=True))
    op.add_column("partner_registrations", sa.Column("account_number", sa.String(length=30), nullable=True))
    op.add_column("partner_registrations", sa.Column("ifsc_code", sa.String(length=20), nullable=True))
    op.add_column("partner_registrations", sa.Column("gst_certificate_path", sa.String(length=500), nullable=True))
    op.add_column("partner_registrations", sa.Column("pan_card_path", sa.String(length=500), nullable=True))
    op.add_column("partner_registrations", sa.Column("cancelled_cheque_path", sa.String(length=500), nullable=True))
    op.add_column("partner_registrations", sa.Column("msme_certificate_path", sa.String(length=500), nullable=True))
    op.add_column("partner_registrations", sa.Column("address_proof_path", sa.String(length=500), nullable=True))
    op.add_column("partner_registrations", sa.Column("incorporation_certificate_path", sa.String(length=500), nullable=True))
    op.add_column("partner_registrations", sa.Column("aadhaar_card_path", sa.String(length=500), nullable=True))
    op.add_column("partner_registrations", sa.Column("photo_path", sa.String(length=500), nullable=True))
    op.add_column(
        "partner_registrations",
        sa.Column("declaration_accepted", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    for col in (
        "declaration_accepted",
        "photo_path",
        "aadhaar_card_path",
        "incorporation_certificate_path",
        "address_proof_path",
        "msme_certificate_path",
        "cancelled_cheque_path",
        "pan_card_path",
        "gst_certificate_path",
        "ifsc_code",
        "account_number",
        "account_holder_name",
        "bank_branch",
        "bank_name",
        "product_categories",
        "operating_states",
        "annual_turnover",
        "year_of_establishment",
        "aadhaar_no",
        "cin_no",
        "udyam_no",
        "website",
        "district",
        "alternate_mobile",
        "contact_designation",
        "business_type",
    ):
        op.drop_column("partner_registrations", col)
