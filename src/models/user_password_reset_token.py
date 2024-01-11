from src import db

from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import func, text, ForeignKey


class UserPasswordResetToken(db.Model):
    """
    Model for user_password_reset_token table
    Attributes:
    'token': Unique password reset token (VARCHAR(512)) PK
    'user_id': Unique identifier for user (UUID) FK
    'created_at': Timestamp for creation of token (TIMESTAMP)
    'used_at': Timestamp for use of token (TIMESTAMP)
    'is_valid': Boolean check if token is valid (BOOLEAN)
    """
    __tablename__ = 'user_password_reset_token'

    token = db.Column(db.String(512), primary_key=True, nullable=False,
        comment='base64 URL encoded token for password reset')
    user_id = db.Column(UUID(as_uuid=True), ForeignKey("user.user_id"), 
        nullable=False,  
        comment='User ID that generated the token')
    created_at = db.Column(db.DateTime, server_default=func.now(), 
        comment='Timestamp for creation of token')
    used_at = db.Column(db.DateTime, 
        comment='Timestamp for use/consumption of token')
    is_valid =  db.Column(db.Boolean, server_default='true', 
        comment='Boolean check if token is valid')
    
    # Constructor initializing values.
    def __init__(self, token, user_id):
        self.token = token,
        self.user_id = user_id
