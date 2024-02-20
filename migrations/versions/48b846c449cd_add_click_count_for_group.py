"""add click count for group

Revision ID: 48b846c449cd
Revises: 880cb8c8c2ba
Create Date: 2024-02-20 17:05:30.246623

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "48b846c449cd"
down_revision = "880cb8c8c2ba"
branch_labels = None
depends_on = None


def upgrade():
    # Add the new columns
    op.add_column(
        "groups",
        sa.Column("click_count", sa.Integer(), nullable=True, server_default="0"),
    )
    op.add_column(
        "groups",
        sa.Column("receiver_count", sa.Integer(), nullable=True, server_default="0"),
    )

    op.add_column(
        "groups",
        sa.Column(
            "profile_receiver_count", sa.Integer(), nullable=True, server_default="0"
        ),
    )

    op.add_column(
        "groups",
        sa.Column(
            "profile_giver_count", sa.Integer(), nullable=True, server_default="0"
        ),
    )


def downgrade():
    # Remove the new columns
    op.drop_column("groups", "click_count")
    op.drop_column("groups", "receiver_count")
    op.drop_column("groups", "profile_receiver_count")
    op.drop_column("groups", "profile_giver_count")
