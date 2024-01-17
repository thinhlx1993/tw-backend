"""add force_start for missions

Revision ID: 1ad0f437d2e1
Revises: 02d4121e1332
Create Date: 2024-01-18 02:29:08.375332

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "1ad0f437d2e1"
down_revision = "02d4121e1332"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "mission",
        sa.Column("force_start", sa.Boolean(), server_default="false", nullable=True),
    )


def downgrade():
    op.drop_column("mission", "force_start")
