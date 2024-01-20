"""enable default for profiles

Revision ID: 62cb04dc14eb
Revises: 308c788237e1
Create Date: 2024-01-21 03:03:29.910302

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "62cb04dc14eb"
down_revision = "308c788237e1"
branch_labels = None
depends_on = None

columns_modify = [
    "user_access",
    "username",
    "name",
    "password",
    "fa",
    "proxy",
    "gpt_key",
    "cookies",
    "cookies",
    "notes",
    "browser_data",
    "status",
    "hma_profile_id",
    "emails",
    "pass_emails",
    "phone_number",
]


def upgrade():
    for item in columns_modify:
        op.alter_column(
            "profiles",
            item.strip(),
            existing_type=sa.String(length=128),
            server_default="",
            existing_nullable=True,
        )


def downgrade():
    for item in columns_modify:
        op.alter_column(
            "profiles",
            item.strip(),
            existing_type=sa.String(length=128),
            server_default=None,
            existing_nullable=True,
        )
