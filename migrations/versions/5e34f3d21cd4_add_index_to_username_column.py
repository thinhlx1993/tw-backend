"""Add index to username column

Revision ID: 5e34f3d21cd4
Revises: 392494e8a311
Create Date: 2024-03-02 16:38:47.328475

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "5e34f3d21cd4"
down_revision = "392494e8a311"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index("idx_profiles_username", "profiles", ["username"], unique=True)


def downgrade():
    op.drop_index("idx_profiles_username", table_name="profiles")
