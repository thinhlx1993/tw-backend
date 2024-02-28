"""add teams plan for team

Revision ID: 308c788237e1
Revises: 51990b20df76
Create Date: 2024-01-21 01:51:08.090574

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "308c788237e1"
down_revision = "51990b20df76"
branch_labels = None
depends_on = None


def upgrade():
    # pass
    op.add_column(
        "teams",
        sa.Column("teams_plan", sa.Integer, server_default="100", nullable=True),
        schema="public",
    )


def downgrade():
    # pass
    op.drop_column("teams", "teams_plan", schema="public")
