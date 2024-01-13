"""add profiles table

Revision ID: 5234b5eccc9c
Revises: 91dede4a905b
Create Date: 2024-01-12 02:24:56.636541

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Inspector

# revision identifiers, used by Alembic.
revision = '5234b5eccc9c'
down_revision = '91dede4a905b'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    # if 'profiles' not in tables:

    op.create_table(
        'groups',
        sa.Column(
            'group_id',
            sa.String(length=128),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False
        ),
        sa.Column('group_name', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('modified_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('group_id')
    )

    op.create_table(
        'profiles',
        sa.Column(
            'profile_id',
            sa.String(length=128),
            server_default=sa.text('uuid_generate_v4()'),
            nullable=False
        ),
        sa.Column(
            'group_id',
            sa.String(length=128),
            nullable=True
        ),
        sa.Column('username', sa.String(length=128), nullable=True, unique=True),
        sa.Column('name', sa.String(length=128), nullable=True),
        sa.Column('password', sa.String(length=128), nullable=True),
        sa.Column('fa', sa.String(length=128), nullable=True),
        sa.Column('proxy', sa.String(length=128), nullable=True),
        sa.Column('gpt_key', sa.String(length=128), nullable=True),
        sa.Column('cookies', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('profile_data', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('modified_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.group_id'], ),
        sa.PrimaryKeyConstraint('profile_id')
    )


def downgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()
    # if 'profiles' in tables:
    op.drop_table('profiles')
    # if 'groups' in tables:
    op.drop_table('groups')
