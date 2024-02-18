"""add group user fk

Revision ID: 8c8d680aba0a
Revises: 40bf9ca78a0d
Create Date: 2024-02-18 10:29:19.172109

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "8c8d680aba0a"
down_revision = "40bf9ca78a0d"
branch_labels = None
depends_on = None


def upgrade():
    # Use batch_alter_table for compatibility with SQLite
    with op.batch_alter_table("groups") as batch_op:
        batch_op.alter_column(
            "user_id",
            existing_type=sa.String(length=128),
            type_=sa.String(length=128),
            existing_nullable=True,
            nullable=True,
        )
        batch_op.create_foreign_key("fk_groups_users", "user", ["user_id"], ["user_id"])


def downgrade():
    with op.batch_alter_table("groups") as batch_op:
        batch_op.drop_constraint("fk_groups_users", type_="foreignkey")
