"""add new field for profiles table

Revision ID: 201f8dd5e0e2
Revises: 0654d3da7301
Create Date: 2024-01-19 11:07:17.436618

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '201f8dd5e0e2'
down_revision = '0654d3da7301'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('profiles', sa.Column('hma_profile_id', sa.String(length=128), nullable=True))
    op.add_column('profiles', sa.Column('emails', sa.String(length=128), nullable=True))
    op.add_column('profiles', sa.Column('pass_emails', sa.String(length=128), nullable=True))
    op.add_column('profiles', sa.Column('phone_number', sa.String(length=128), nullable=True))


def downgrade():
    op.drop_column('profiles', 'phone_number')
    op.drop_column('profiles', 'emails')
    op.drop_column('profiles', 'pass_emails')
    op.drop_column('profiles', 'hma_profile_id')