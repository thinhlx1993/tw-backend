from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func, text, ForeignKey
from sqlalchemy.dialects.postgresql import BYTEA

from src import db
# Creating User class that maps to table 'user'


class UserPreference(db.Model):
    """
    Model for user Table
    Attributes:
    'preference_id' : Unique ID generated for each preference(UUID)
    'user_id' : User ID of preference(UUID)
    'modified_at' : Timestamp for update of record(DATETIME)
    'default_page' : Default page to serve user(VARCHAR(128))
    'notifications_enabled' : Boolean check if user has notifications enabled(BOOLEAN)
    'added_at' : Timestamp for user added to teams(DATETIME)
    'grafana_url': Dashboard url(STRING)
    """
    __tablename__ = 'user_preference'

    preference_id = db.Column(db.String(128), server_default=text(
        "uuid_generate_v4()"), primary_key=True, nullable=False)
    user_id = db.Column(db.String(128), ForeignKey('user.user_id'))
    modified_at = db.Column(db.DateTime, server_default=func.now())
    default_page = db.Column(db.String(128))
    is_disabled = db.Column(db.Boolean, server_default='false')
    notifications_enabled = db.Column(db.Boolean)
    added_at = db.Column(db.DateTime, server_default=func.now())
    grafana_url = db.Column(db.String(128))
    
    # Constructor initializing values.

    def __init__(self, user_id):
        self.user_id = user_id
        
    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        """
        String representation for results fetched from the table
        """
        return str("{'preferene_id':" + str(self.preference_id) + 
            ", 'user_id':" + str(self.user_id) + 
            ", 'modified_at':" + str(self.modified_at) + 
            ", 'default_page':" + str(self.default_page) + 
            ", 'is_disabled':" + str(self.is_disabled) + 
            ", 'notifications_enabled':" + str(self.notifications_enabled)  + 
            ", 'added_at':" + str(self.added_at) + 
            ", 'grafana_url':" + str(self.grafana_url) + 
            "}")
    
    def repr_name(self):
        """Dict representation of user_preference model"""
        return {
            'preference_id': str(self.preference_id),
            'user_id': str(self.user_id),
            'added_at': self.added_at
        }
