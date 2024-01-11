from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import text
from sqlalchemy.types import String

from src import db
# Creating AuthTokenBlacklist class that maps to table 'auth_token_blacklist'


class AuthTokenBlacklist(db.Model):
    """
    Model for auth token blacklist Table
    Attributes:
    'token_id' : jti for token
    """
    __tablename__ = 'auth_token_blacklist'

    token_id = db.Column(UUID(as_uuid=True), primary_key=True, nullable=False)

    # Constructor initializing values.
    def __init__(self, token_id):
        self.token_id = token_id
