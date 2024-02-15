"""add owner pk

Revision ID: 40bf9ca78a0d
Revises: 08e69bd9f14a
Create Date: 2024-02-16 00:11:05.155991

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "40bf9ca78a0d"
down_revision = "08e69bd9f14a"
branch_labels = None
depends_on = None


def upgrade():
    # Use batch_alter_table for compatibility with SQLite
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.alter_column(
            "owner",
            existing_type=sa.String(length=128),
            type_=sa.String(length=128),
            existing_nullable=True,
            nullable=True,
        )
        batch_op.create_foreign_key(
            "fk_profiles_owner_user", "user", ["owner"], ["user_id"]
        )


def downgrade():
    with op.batch_alter_table("profiles") as batch_op:
        batch_op.drop_constraint("fk_profiles_owner_user", type_="foreignkey")
