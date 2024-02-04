"""add username for posts

Revision ID: 33a1719ead61
Revises: e90b725b9a7f
Create Date: 2024-02-04 18:23:43.748395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "33a1719ead61"
down_revision = "e90b725b9a7f"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "posts",
        sa.Column("username", sa.String(128), server_default="", nullable=True),
    )


def downgrade():
    op.drop_column("posts", "username")
