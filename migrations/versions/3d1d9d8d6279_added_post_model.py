"""Added post model

Revision ID: 3d1d9d8d6279
Revises: a16283a5bc21
Create Date: 2024-01-24 23:01:31.817980

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "3d1d9d8d6279"
down_revision = "a16283a5bc21"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "posts",
        sa.Column("post_id", sa.String(length=128), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("tw_post_id", sa.String(length=255), nullable=False),
        sa.Column("profile_id", sa.String(length=128), nullable=False),
        sa.Column("crawl_by", sa.String(length=128), nullable=False),
        sa.Column("like", sa.String(length=128), nullable=False),
        sa.Column("comment", sa.String(length=128), nullable=False),
        sa.Column("share", sa.String(length=128), nullable=False),
        sa.Column("view", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["profiles.profile_id"]),
        sa.ForeignKeyConstraint(["crawl_by"], ["user.user_id"]),
        sa.PrimaryKeyConstraint("post_id"),
    )


def downgrade():
    op.drop_table("posts")
