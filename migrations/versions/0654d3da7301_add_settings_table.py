"""Add settings table

Revision ID: 0654d3da7301
Revises: 1ad0f437d2e1
Create Date: 2024-01-19 00:14:49.182363

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0654d3da7301"
down_revision = "1ad0f437d2e1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "settings",
        sa.Column("user_id", sa.String(length=128), nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column("settings", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.user_id"],
        ),
        sa.PrimaryKeyConstraint("user_id", "device_id"),
    )


def downgrade():
    op.drop_table("settings")
