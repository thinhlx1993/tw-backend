"""add main profile

Revision ID: 9c999aabacd1
Revises: 3b0ae7459be3
Create Date: 2024-01-28 22:03:05.435588

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9c999aabacd1"
down_revision = "3b0ae7459be3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "profiles",
        sa.Column("main_profile", sa.Boolean(), server_default="false", nullable=True),
    )


def downgrade():
    op.drop_column("profiles", "main_profile")
