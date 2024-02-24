"""add tz data

Revision ID: b955c8928290
Revises: 48b846c449cd
Create Date: 2024-02-24 09:00:41.512339

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b955c8928290'
down_revision = '48b846c449cd'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "profiles",
        sa.Column("tz_info", sa.JSON(), nullable=True),
    )


def downgrade():
    op.drop_column("profiles", "tz_info")
