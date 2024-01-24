"""add owner for profiles

Revision ID: e9a047c5d9fa
Revises: b8d4106f82a8
Create Date: 2024-01-24 12:00:08.465453

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e9a047c5d9fa"
down_revision = "b8d4106f82a8"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "profiles",
        sa.Column("owner", sa.String(length=128), server_default="", nullable=True),
    )


def downgrade():
    op.drop_column("profiles", "owner")
