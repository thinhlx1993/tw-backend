"""add soft delete for posts

Revision ID: 962d9df9a1cb
Revises: 33a1719ead61
Create Date: 2024-02-04 19:51:23.627538

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "962d9df9a1cb"
down_revision = "33a1719ead61"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "posts",
        sa.Column("is_deleted", sa.Boolean(), server_default="false", nullable=True),
    )


def downgrade():
    op.drop_column("posts", "is_deleted")
