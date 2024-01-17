"""add user_id for mission

Revision ID: ecdd09cde259
Revises: 328d488b9103
Create Date: 2024-01-17 18:22:57.727121

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ecdd09cde259'
down_revision = '328d488b9103'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "mission", sa.Column("user_id", sa.String(length=128), nullable=False)
    )


def downgrade():
    op.drop_column(
        "mission", "user_id"
    )
