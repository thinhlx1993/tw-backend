"""Add today_post_count column to Profiles

Revision ID: 919fae805ad1
Revises: 5e34f3d21cd4
Create Date: 2024-03-06 02:50:50.586516

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "919fae805ad1"
down_revision = "5e34f3d21cd4"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "profiles",
        sa.Column("today_post_count", sa.Integer(), nullable=True, server_default="0"),
    )


def downgrade():
    op.drop_column("profiles", "today_post_count")
