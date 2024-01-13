from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import func, text

from src import db
# Creating User class that maps to table 'user'


class UserDetails(db.Model):
    """
    Model for user details Table
    Attributes:
    'user_id' : Unique ID generated for each user(UUID)
    'username' : Registered Username of user(VARCHAR(256))
    'email' : Registered email address of user(VARCHAR(256))
    'password' : Encrypted password of user(VARCHAR(256))
    'first_name' : First name of user(VARCHAR(128))
    'last_name' : Last name of user(VARCHAR(128))
    'default_page' : Default page to serve user(VARCHAR(128))
    'is_disabled' : Boolean check if user is disabled(BOOLEAN)
    'notifications_enabled' : Boolean check if user has 
    notifications enabled(BOOLEAN)
    'phone_number' : Phone number of user(VARCHAR(128))
    'country_id' : Country ID of user(UUID)
    'added_at' : TIMESTAMP when the user was added to the teams(DATETIME)
    """
    __tablename__ = 'user_details'

    user_id = db.Column(db.String(128), server_default=text(
        "uuid_generate_v4()"), primary_key=True, nullable=False)
    username = db.Column(db.String(256), nullable=False, unique=True)
    email = db.Column(db.String(256))
    password = db.Column(db.String(512))
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    default_page = db.Column(db.String(128))
    is_disabled = db.Column(db.Boolean, server_default='false')
    notifications_enabled = db.Column(db.Boolean)
    phone_number = db.Column(db.String(128))
    
    # Constructor initializing values.
    def __init__(self, username, email, password, first_name,
                 last_name, default_page,
                 is_disabled, notifications_enabled, phone_number, 
                 is_email_verified, country_id, added_at):
        self.username = username
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.default_page = default_page
        self.is_disabled = is_disabled
        self.notifications_enabled = notifications_enabled
        self.phone_number = phone_number
        self.country_id = country_id

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        """
        String representation for results fetched from the table
        """
        return str(self.repr_name())

    def repr_name(self):
        return {
            "user_id": str(self.user_id),
            "username": self.username
        }