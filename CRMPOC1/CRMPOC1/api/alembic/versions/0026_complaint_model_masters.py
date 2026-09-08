"""Seed complaint model master rows in item_masters.

Revision ID: 0026_complaint_model_masters
Revises: 0025_engineer_completion_code
Create Date: 2026-08-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0026_complaint_model_masters"
down_revision: Union[str, None] = "0025_engineer_completion_code"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

COMPLAINT_MODEL_CATEGORY = "Complaint Model"
COMPLAINT_MODEL_ITEMS = [
    ("IDC-CM-WAC", "Window AC"),
    ("IDC-CM-SAC", "Split AC"),
    ("IDC-CM-FRG", "Fridge"),
    ("IDC-CM-GYS", "Geyser"),
    ("IDC-CM-WCL", "Water Cooler"),
    ("IDC-CM-ACL", "Air Cooler"),
]


def upgrade() -> None:
    conn = op.get_bind()
    for code, name in COMPLAINT_MODEL_ITEMS:
        exists = conn.execute(
            sa.text("SELECT 1 FROM item_masters WHERE item_code = :code LIMIT 1"),
            {"code": code},
        ).first()
        if exists:
            continue
        conn.execute(
            sa.text(
                """
                INSERT INTO item_masters (
                    item_code, item_name, category, serial_count, is_active, created_at, updated_at
                ) VALUES (
                    :code, :name, :category, 1, 1, CURRENT_TIMESTAMP(6), CURRENT_TIMESTAMP(6)
                )
                """
            ),
            {"code": code, "name": name, "category": COMPLAINT_MODEL_CATEGORY},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for code, _name in COMPLAINT_MODEL_ITEMS:
        conn.execute(
            sa.text("DELETE FROM item_masters WHERE item_code = :code"),
            {"code": code},
        )
