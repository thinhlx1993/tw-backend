from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import BYTEA

from src import db


# Creating User class that maps to table 'user'


class User(db.Model):
    """
    Model for user Table
    Attributes:
    'user_id' : Unique ID generated for each user(UUID)
    'username' : Registered Username of user(VARCHAR(256))
    'email' : Registered email address of user(VARCHAR(256))
    'password' : Encrypted password of user(VARCHAR(256))
    'first_name' : First name of user(VARCHAR(128))
    'last_name' : Last name of user(VARCHAR(128))
    'created_at' : Timestamp for creation of user(DATETIME)
    'default_page' : Default page to serve user(VARCHAR(128))
    'is_disabled' : Boolean check if user is disabled(BOOLEAN)
    'notifications_enabled' : Boolean check if user has 
    notifications enabled(BOOLEAN)
    'mfa_enabled' : Boolean check if user has multifactor auth enabled(BOOLEAN)
    'phone_number' : Phone number of user(VARCHAR(128))
    'is_email_verified' : Boolean check if user email is verified disabled(BOOLEAN)
    'country_id' : Country ID of user(UUID)
    'last_active_at' : Timestamp of last login or token refresh(DATETIME)
    """
    __tablename__ = 'user'

    user_id = db.Column(UUID(as_uuid=True), server_default=text(
        "uuid_generate_v4()"), primary_key=True, nullable=False)
    username = db.Column(db.String(256), nullable=False, unique=True)
    email = db.Column(db.String(256))
    password = db.Column(db.String(512))
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, server_default=func.now())
    default_page = db.Column(db.String(128))
    is_disabled = db.Column(db.Boolean, server_default='false')
    notifications_enabled = db.Column(db.Boolean)
    mfa_enabled = db.Column(db.Boolean, server_default='false')
    mfa_secret = db.Column(BYTEA)
    phone_number = db.Column(db.String(128))
    is_email_verified = db.Column(db.Boolean, server_default='false')
    country_id = db.Column(UUID(as_uuid=True))
    last_active_at = db.Column(db.DateTime, server_default=func.now())
    password_reset_tokens = relationship("UserPasswordResetToken", backref="user")
    user_roles = relationship(
        "UserRole", secondary="user_role_mapping", back_populates="users"
    )
    # user_teams = relationship( 'Teams', secondary="teams")
    user_teams_mapping = relationship(
        "Teams",
        secondary="user_teams_mapping",
        back_populates="teams_user_mapping",
    )

    # Constructor initializing values.
    def __init__(self, username, password, first_name, last_name):
        self.username = username
        self.password = password
        self.first_name = first_name
        self.last_name = last_name

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        """
        String representation for results fetched from the table
        """
        return str("{'user_id':" + str(self.user_id) + ", 'username':" +
                   self.username + ", 'email':" + str(self.email) +
                   ", 'first_name':" + str(self.first_name) +
                   ", 'last_name':" + str(self.last_name) + ", 'created_at':" + str(self.created_at) +
                   ", 'default_page':" + str(self.default_page) + ", 'is_disabled':" +
                   str(self.is_disabled) + ", 'notifications_enabled':" +
                   str(self.notifications_enabled) + ", 'phone_number':" +
                   str(self.phone_number) + ", 'is_email_verified':" +
                   str(self.is_email_verified) + ", 'country_id':" +
                   str(self.country_id) + ", 'last_active_at':" +
                   str(self.last_active_at) + "}")

    def repr_name(self):
        """dict representation of user row"""
        return {
            'user_id': str(self.user_id),
            'username': str(self.username),
            'email': str(self.email),
            'first_name': str(self.first_name),
            'last_name': str(self.last_name),
            'created_at': str(self.created_at),
            'is_disabled': str(self.is_disabled),
            'phone_number': str(self.phone_number),
            'is_email_verified': str(self.is_email_verified),
            'last_active_at': str(self.last_active_at),
            'is_admin': True if [role for role in self.user_roles if role.role_name == 'admin'] else False
        }
