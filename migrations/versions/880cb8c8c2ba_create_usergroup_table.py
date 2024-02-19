"""Create UserGroup table

Revision ID: 880cb8c8c2ba
Revises: 7673e33cddb8
Create Date: 2024-02-19 18:28:09.785105

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "880cb8c8c2ba"
down_revision = "7673e33cddb8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "user_group",
        sa.Column(
            "user_id", sa.String(128), sa.ForeignKey("user.user_id"), primary_key=True
        ),
        sa.Column(
            "group_id",
            sa.String(128),
            sa.ForeignKey("groups.group_id"),
            primary_key=True,
        ),
    )


def downgrade():
    op.drop_table("user_group")
