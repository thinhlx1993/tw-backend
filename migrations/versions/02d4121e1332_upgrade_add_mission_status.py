"""upgrade add mission status

Revision ID: 02d4121e1332
Revises: c0755a449748
Create Date: 2024-01-18 00:15:47.146891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "02d4121e1332"
down_revision = "c0755a449748"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("mission", sa.Column("status", sa.String(length=128), nullable=True))


def downgrade():
    op.drop_column("mission", "status")
