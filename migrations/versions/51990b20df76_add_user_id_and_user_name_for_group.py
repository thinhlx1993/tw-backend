"""add user id and user name for group

Revision ID: 51990b20df76
Revises: c43547477a0f
Create Date: 2024-01-20 16:56:00.428935

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51990b20df76'
down_revision = 'c43547477a0f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('groups', sa.Column('user_id', sa.String(length=128), nullable=True))
    op.add_column('profiles', sa.Column('user_access', sa.String(length=128), nullable=True))
    op.add_column('groups', sa.Column('username', sa.String(length=128), nullable=True))


def downgrade():
    op.drop_column('groups', 'user_id')
    op.drop_column('profiles', 'user_access')
    op.drop_column('groups', 'username')
