"""Model for UserRoleMapping table."""

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

from src import db
# Creating UserRoleMapping class that maps to user_role_mapping table


class UserRoleMapping(db.Model):
    """Model for user_role_mapping table.

    Attributes:
    'user_id': User ID(UUID)
    'role_id': Role ID(UUID)
    'teams_id': Teams ID(UUID)
    """
    __tablename__ = 'user_role_mapping'

    # Table does not have Primary key(PK), but SQLAlchemy requires
    # table to have one. Hence, both have been set to PK.
    user_id = db.Column(db.String(128), ForeignKey("user.user_id"),
                        primary_key=True, nullable=False)
    role_id = db.Column(db.String(128), ForeignKey("user_role.role_id"),
                        primary_key=True, nullable=False,)
    teams_id = db.Column(db.String(128), ForeignKey("teams.teams_id"),
                        primary_key=True, nullable=False,)
    __table_args__ = (UniqueConstraint(
        'user_id', 'role_id', 'teams_id', name='_user_role_teams_uc'),)

    # Constructor initializing values
    def __init__(self, user_id, role_id, teams_id):
        self.user_id = user_id
        self.role_id = role_id
        self.teams_id = teams_id

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        return str("{'user_id':" + str(self.user_id) + ", 'role_id':"
                   + str(self.role_id) + "}")

    def repr_name(self):
        """Custom representation of user_role_mapping row."""
        return {
            "user_id": self.user_id,
            "role_id": self.role_id,
            "teams_id": self.teams_id
        }
