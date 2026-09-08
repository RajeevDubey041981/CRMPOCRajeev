"""add sub_module to permissions

Revision ID: 0002_submodule
Revises: 0001_initial
Create Date: 2026-05-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_submodule"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "permissions",
        sa.Column("sub_module", sa.String(100), nullable=True),
    )
    # Postgres treats NULLs as distinct under standard UNIQUE constraints, so we
    # use a partial expression-index to enforce one row per (role, module, sub_module)
    # with NULL collapsed to empty string.
    op.execute(
        "CREATE UNIQUE INDEX uq_permissions_role_module_sub "
        "ON permissions (role_id, module, COALESCE(sub_module, ''))"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_permissions_role_module_sub")
    op.drop_column("permissions", "sub_module")
