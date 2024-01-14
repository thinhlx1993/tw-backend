"""add tasks

Revision ID: 328d488b9103
Revises: 9a0b7cc179aa
Create Date: 2024-01-14 16:36:24.952007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '328d488b9103'
down_revision = '9a0b7cc179aa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # (other migration commands)

    # Insert default tasks
    task_names = [
        "Login", "Lấy cookie", "Giải captra", "Check follow", "Check tích xanh",
        "Check bật kiếm tiền", "Lấy link bài viết", "Thay số điện thoại", "Thay emails"
    ]

    tasks_table = sa.table('tasks',
        sa.column('tasks_id', sa.String(length=128)),
        sa.column('tasks_name', sa.String(length=256))
    )

    for name in task_names:
        op.bulk_insert(tasks_table, [{'tasks_name': name}])
    # ### end Alembic commands ###


def downgrade():
    pass
