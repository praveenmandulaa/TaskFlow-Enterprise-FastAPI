"""create refresh sessions table

Revision ID: db12a7da8896
Revises: 72ee04cd139b
Create Date: 2026-10-28 23:29:17.648134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'db12a7da8896'
down_revision: Union[str, Sequence[str], None] = '72ee04cd139b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    pass


def downgrade() -> None:
    op.drop_index(
        "ix_refresh_sessions_user_id",
        table_name="refresh_sessions",
    )
    op.drop_table("refresh_sessions")
