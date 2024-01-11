"""Model for teams table."""

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src import db
# Creating User class that maps to table 'user'


class Teams(db.Model):
    """Model for teams table.

    Attributes:
    'teams_id': Unique ID generated for each teams(UUID)
    'teams_name': Teams name(VARCHAR(256))
    'teams_code': Unique teams code(VARCHAR(256))
    'owner': Userid of owner of the teams (UUID)
    'created_at': Timestamp for creation of teams(DATETIME)
    'updated_at': Timestamp for update of teams(DATETIME)
    'is_disabled': Boolean check if teams is disabled(BOOLEAN)
    'is_deleted': Boolean check if teams is deleted(BOOLEAN)
    """
    __tablename__ = 'teams'

    teams_id = db.Column(
        UUID(as_uuid=True), server_default=text("uuid_generate_v4()"),
        primary_key=True, nullable=False)
    teams_name = db.Column(db.String(256), nullable=False)
    teams_code = db.Column(db.String(256))
    owner = db.Column(UUID(as_uuid=True))
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime, server_default=func.now())
    is_disabled = db.Column(db.Boolean, server_default='false')
    is_deleted = db.Column(db.Boolean, server_default='false')

    teams_user_mapping = relationship(
        "User",
        secondary="user_teams_mapping",
        back_populates="user_teams_mapping",
    )

    # Constructor initializing values.
    def __init__(self, teams_name, teams_code, owner):
        self.teams_name = teams_name
        self.teams_code = teams_code
        self.owner = owner

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        """String representation for results fetched from the table."""
        return str("{'teams_id':" + str(self.teams_id)
            + ",       'teams_code:" + str(self.teams_code).lower()
            + ",       'teams_name':" + self.teams_name
            + ", 'owner':" + str(self.owner) + ", 'is_disabled':"
            + str(self.is_disabled) + ", 'id_deleted':" + str(self.is_deleted)
            + "}")

    def repr_name(self):
        """Dict representation for Teams row"""
        return {
            "teams_id" : str(self.teams_id),
            "teams_name": str(self.teams_name),
            "teams_code": str(self.teams_code).lower(),
            "owner": str(self.owner),
            "is_disabled": str(self.is_disabled),
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at)
        }