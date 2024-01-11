"""Update user metadata

Revision ID: cbb01f1b3707
Revises: 43c4bd8f3a7e
Create Date: 2023-12-15 18:15:48.793979

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cbb01f1b3707'
down_revision = '43c4bd8f3a7e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('last_activate_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True))
    op.add_column('users', sa.Column('language', sa.String(length=128), server_default='english', nullable=True))
    op.add_column('users', sa.Column('subscription', sa.String(length=128), server_default='free', nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'subscription')
    op.drop_column('users', 'language')
    op.drop_column('users', 'last_activate_at')
    # ### end Alembic commands ###
