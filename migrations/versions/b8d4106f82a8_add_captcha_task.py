"""add captcha task

Revision ID: b8d4106f82a8
Revises: 62cb04dc14eb
Create Date: 2024-01-24 00:32:41.304024

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b8d4106f82a8"
down_revision = "62cb04dc14eb"
branch_labels = None
depends_on = None


def upgrade():
    task_names = ["Giải Captcha"]

    tasks_table = sa.table(
        "tasks",
        sa.column("tasks_id", sa.String(length=128)),
        sa.column("tasks_name", sa.String(length=256)),
    )

    for name in task_names:
        op.bulk_insert(tasks_table, [{"tasks_name": name}])


def downgrade():
    pass
