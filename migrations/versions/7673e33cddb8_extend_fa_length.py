"""extend fa length

Revision ID: 7673e33cddb8
Revises: 40bf9ca78a0d
Create Date: 2024-02-19 14:55:12.270714

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7673e33cddb8'
down_revision = '40bf9ca78a0d'
branch_labels = None
depends_on = None


def upgrade():
    # Use op.alter_column to modify the column
    op.alter_column('profiles', 'fa', type_=sa.Text())


def downgrade():
    # In case of downgrade, revert the changes
    op.alter_column('profiles', 'fa', type_=sa.String(length=128))