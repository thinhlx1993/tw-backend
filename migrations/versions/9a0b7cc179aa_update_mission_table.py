"""update mission table

Revision ID: 9a0b7cc179aa
Revises: 5234b5eccc9c
Create Date: 2024-01-14 16:14:46.622144

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "9a0b7cc179aa"
down_revision = "5234b5eccc9c"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint("mission_robot_id_fkey", "mission", type_="foreignkey")
    op.drop_column("mission", "robot_id")
    op.add_column(
        "mission", sa.Column("group_id", sa.String(length=128), nullable=True)
    )
    op.create_foreign_key(
        "mission_group_id_fkey", "mission", "groups", ["group_id"], ["group_id"]
    )

    op.create_table(
        "tasks",
        sa.Column(
            "tasks_id",
            sa.String(128),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.Column("tasks_name", sa.String(length=256), nullable=True),
        sa.Column(
            "tasks_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="JSON for tasks",
        ),
        sa.PrimaryKeyConstraint("tasks_id"),
    )
    op.create_table(
        "mission_tasks",
        sa.Column("mission_id", sa.String(length=128), nullable=False),
        sa.Column("tasks_id", sa.String(length=128), nullable=False),
        sa.ForeignKeyConstraint(
            ["mission_id"],
            ["mission.mission_id"],
        ),
        sa.ForeignKeyConstraint(
            ["tasks_id"],
            ["tasks.tasks_id"],
        ),
        sa.PrimaryKeyConstraint("mission_id", "tasks_id"),
    )


def downgrade():
    op.drop_constraint("mission_group_id_fkey", "mission", type_="foreignkey")
    op.drop_column("mission", "group_id")

    op.add_column(
        "mission", sa.Column("robot_id", sa.String(length=128), nullable=False)
    )
    op.create_foreign_key(
        "mission_robot_id_fkey", "mission", "robot", ["robot_id"], ["robot_id"]
    )
    op.drop_table('mission_tasks')
    op.drop_table("tasks")
