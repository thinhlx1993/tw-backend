"""Change data type of cookies column to Text

Revision ID: 392494e8a311
Revises: 0c1ff67c2f43
Create Date: 2024-03-02 16:21:06.891777

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "392494e8a311"
down_revision = "0c1ff67c2f43"
branch_labels = None
depends_on = None


def upgrade():
    # Your previous upgrade code here
    op.alter_column(
        "profiles",
        "cookies",
        existing_type=sa.String(length=128),
        type_=sa.Text(),
        existing_nullable=True,
        server_default="",
    )


def downgrade():
    # Your previous downgrade code here
    op.alter_column(
        "profiles",
        "cookies",
        existing_type=sa.Text(),
        type_=sa.String(length=128),
        existing_nullable=True,
        server_default="",
    )
