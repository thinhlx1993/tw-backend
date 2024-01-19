"""add browser data for profiles

Revision ID: c43547477a0f
Revises: 201f8dd5e0e2
Create Date: 2024-01-19 17:50:29.671506

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c43547477a0f'
down_revision = '201f8dd5e0e2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('profiles', sa.Column('browser_data', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('profiles', 'browser_data')
