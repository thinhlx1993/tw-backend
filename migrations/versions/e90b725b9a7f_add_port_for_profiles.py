"""add port for profiles

Revision ID: e90b725b9a7f
Revises: 9c999aabacd1
Create Date: 2024-01-31 09:30:23.405941

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e90b725b9a7f"
down_revision = "9c999aabacd1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "profiles",
        sa.Column("debugger_port", sa.String(length=128), nullable=True),
    )


def downgrade():
    op.drop_column("profiles", "debugger_port")
