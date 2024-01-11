"""add created_by

Revision ID: 1fe6e7d1b8dd
Revises: caaf5832fd24
Create Date: 2023-12-23 00:57:29.860879

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1fe6e7d1b8dd'
down_revision = 'caaf5832fd24'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('file_upload', sa.Column('created_by', sa.String(length=128), nullable=True, comment='the user who create this file'))
    op.create_foreign_key(None, 'file_upload', 'users', ['created_by'], ['user_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'file_upload', type_='foreignkey')
    op.drop_column('file_upload', 'created_by')
    # ### end Alembic commands ###
