"""Add order_id to complaints for direct order linking.

Revision ID: 0027_complaint_order_id
Revises: 0026_complaint_model_masters
Create Date: 2026-08-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0027_complaint_order_id"
down_revision: Union[str, None] = "0026_complaint_model_masters"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("complaints", sa.Column("order_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_complaints_order_id_orders",
        "complaints",
        "orders",
        ["order_id"],
        ["id"],
    )
    op.create_index("ix_complaints_order_id", "complaints", ["order_id"])
    op.execute(
        """
        UPDATE complaints c
        INNER JOIN order_items oi ON c.order_item_id = oi.id
        SET c.order_id = oi.order_id
        WHERE c.order_id IS NULL AND c.order_item_id IS NOT NULL
        """
    )


def downgrade() -> None:
    op.drop_index("ix_complaints_order_id", table_name="complaints")
    op.drop_constraint("fk_complaints_order_id_orders", "complaints", type_="foreignkey")
    op.drop_column("complaints", "order_id")
