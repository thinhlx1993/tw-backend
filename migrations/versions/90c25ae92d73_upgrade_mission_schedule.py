"""upgrade mission schedule

Revision ID: 90c25ae92d73
Revises: ecdd09cde259
Create Date: 2024-01-17 19:17:42.491891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90c25ae92d73'
down_revision = 'ecdd09cde259'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column(
        "mission_schedule", "robot_id"
    )
    op.add_column(
        "mission_schedule", sa.Column("profile_id", sa.String(length=128), nullable=True)
    )
    op.create_foreign_key(
        constraint_name="fk_mission_schedule_profile_id",  # Name of the constraint
        source_table="mission_schedule",  # Table to add the constraint to
        referent_table="profiles",  # Table being referenced
        local_cols=['profile_id'],  # Column in the source table
        remote_cols=['profile_id'],  # Column in the referenced table
        ondelete="SET NULL"  # Optional: action on delete
    )



def downgrade():
    op.drop_constraint(
        constraint_name="fk_mission_schedule_profile_id",
        table_name="mission_schedule",
        type_="foreignkey"
    )
    op.drop_column(
        "mission_schedule", "profile_id"
    )
