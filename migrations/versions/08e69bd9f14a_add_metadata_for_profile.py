"""add metadata for profile

Revision ID: 08e69bd9f14a
Revises: c6edbd9892e8
Create Date: 2024-02-11 23:05:43.293175

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08e69bd9f14a'
down_revision = 'c6edbd9892e8'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "profiles",
        sa.Column("click_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column("comment_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column("like_count", sa.Integer(), nullable=True),
    )
    op.add_column(
        "profiles",
        sa.Column("is_disable", sa.Boolean(), server_default="false", nullable=True),
    )


def downgrade():
    op.drop_column("profiles", "click_count")
    op.drop_column("profiles", "comment_count")
    op.drop_column("profiles", "like_count")
    op.drop_column("profiles", "is_disable")
