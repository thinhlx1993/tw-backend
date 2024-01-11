"""Create user password reset token

Revision ID: c3d9a260e572
Revises: fe8bce52d9d6
Create Date: 2020-08-31 13:47:41.503543

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "c3d9a260e572"
down_revision = "f13057818ae2"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names(schema="public")
    if "user_password_reset_token" not in tables:
        op.create_table(
            "user_password_reset_token",
            sa.Column(
                "token_id",
                sa.String(length=128),
                nullable=False,
                comment="primary key id",
                server_default=sa.text('uuid_generate_v4()')
            ),
            sa.Column(
                "token",
                sa.String(length=512),
                nullable=False,
                comment="base64 URL encoded token for password reset",
            ),
            sa.Column(
                "user_id",
                sa.String(length=128),
                nullable=False,
                comment="User ID that generated the token",
            ),
            sa.Column(
                "created_at",
                sa.DateTime(),
                server_default=sa.text("now()"),
                nullable=True,
                comment="Timestamp for creation of token",
            ),
            sa.Column(
                "used_at",
                sa.DateTime(),
                nullable=True,
                comment="Timestamp for use/consumption of token",
            ),
            sa.Column(
                "is_valid",
                sa.Boolean(),
                server_default="true",
                nullable=True,
                comment="Boolean check if token is valid",
            ),
            sa.ForeignKeyConstraint(
                ["user_id"],
                ["users.user_id"],
            ),
            sa.PrimaryKeyConstraint("token_id"),
        )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("user_password_reset_token")
    # ### end Alembic commands ###
