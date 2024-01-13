from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, UniqueConstraint

from src import db
# Creating UserRoleMapping class that maps to user_role_mapping table


class UserTeamsMapping(db.Model):
    """
    Model for user_teams_mapping table
    Attributes:
    'user_id' : User ID(UUID)
    'teams_id': Teams ID(UUID)
    'is_default' : Boolean check default teams for user(BOOLEAN)
    """
    __tablename__ = 'user_teams_mapping'

    # Table does not have Primary key(PK), but SQLAlchemy requires
    # table to have one. Hence, both have been set to PK.
    user_id = db.Column(db.String(128), ForeignKey("user.user_id"),
                        primary_key=True, nullable=False)
    teams_id = db.Column(db.String(128), ForeignKey("teams.teams_id"),primary_key=True, nullable=False)
    is_default = db.Column(db.Boolean, server_default='false')
    __table_args__ = (UniqueConstraint(
        'user_id', 'teams_id', name='_user_teams_uc'),)

    # Constructor initializing values

    # Constructor initializing values
    def __init__(self, user_id, teams_id, is_default):
        self.user_id = user_id
        self.teams_id = teams_id
        self.is_default = is_default

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        return str("{'user_id':" + str(self.user_id) + ", 'teams_id':" +
                   str(self.teams_id) + ",'is_default':" + str(self.is_default) + "}")

    def repr_name(self):
        return str("{'user_id':" + str(self.user_id) + ", 'teams_id':" +
                   str(self.teams_id) + ",'is_default':" + str(self.is_default) + "}")
