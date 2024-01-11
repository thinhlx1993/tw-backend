from sqlalchemy import text, ForeignKey
from src import db
from sqlalchemy import func, text


# Creating AuthTokenBlacklist class that maps to table 'auth_token_blacklist'


class AuthTokenBlacklist(db.Model):
    """
    Model for auth token blacklist Table
    Attributes:
    'token_id' : jti for token
    """

    __tablename__ = "auth_token_blacklist"

    token_id = db.Column(db.String(128), server_default=text(
        "uuid_generate_v4()"), primary_key=True, nullable=False)
    jti = db.Column(db.String(36), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, server_default=func.now())
    revoked = db.Column(db.Boolean, nullable=False)
    user_id = db.Column(
        db.String(128),
        ForeignKey("users.user_id"),
        nullable=False,
        comment="User ID that generated the token",
    )

    # Constructor initializing values.

    def __init__(self, jti, created_at, user_id, revoked):
        self.jti = jti
        self.created_at = created_at
        self.user_id = user_id
        self.revoked = revoked
