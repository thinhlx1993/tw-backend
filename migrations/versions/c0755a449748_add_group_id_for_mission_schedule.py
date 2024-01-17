"""add group_id for mission schedule

Revision ID: c0755a449748
Revises: 90c25ae92d73
Create Date: 2024-01-17 23:08:21.521275

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "c0755a449748"
down_revision = "90c25ae92d73"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "mission_schedule", sa.Column("group_id", sa.String(length=128), nullable=True)
    )
    op.create_foreign_key(
        "mission_schedule_group_id_fkey",
        "mission_schedule",
        "groups",
        ["group_id"],
        ["group_id"],
    )


def downgrade():
    op.drop_constraint(
        "mission_schedule_group_id_fkey", "mission_schedule", type_="foreignkey"
    )
    op.drop_column("mission_schedule", "group_id")
