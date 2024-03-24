"""add date expired for user

Revision ID: 7dffb9826abe
Revises: 3df997d99b5c
Create Date: 2024-03-24 13:52:36.050586

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7dffb9826abe"
down_revision = "3df997d99b5c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("expired_at", sa.DateTime(), nullable=True),
        schema="public",
    )


def downgrade():
    op.drop_column("user", "expired_at", schema="public")
