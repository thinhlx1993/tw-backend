"""add metadata for mission tasks

Revision ID: c6edbd9892e8
Revises: 962d9df9a1cb
Create Date: 2024-02-05 17:56:11.093127

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c6edbd9892e8'
down_revision = '962d9df9a1cb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "mission_tasks",
        sa.Column("config", sa.JSON(), nullable=True),
    )

    op.add_column(
        "mission_tasks",
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True)
    )

    op.add_column(
        "mission",
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=True)
    )


def downgrade():
    op.drop_column("mission_tasks", "config")
    op.drop_column("mission_tasks", "created_at")
    op.drop_column("mission", "created_at")
