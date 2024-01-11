"""Model for UserRoleMappingLog table."""

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID

from src import db
# Creating UserRoleMapping class that maps to user_role_mapping table


class UserRoleMappingLog(db.Model):
    """Model for user_role_mapping_log table.

    Attributes:
    'user_id': User ID(UUID)
    'role_id': Role ID(UUID)
    """
    __tablename__ = 'user_role_mapping_log'

    # Table does not have Primary key(PK), but SQLAlchemy requires
    # table to have one. Hence, both have been set to PK.
    user_id = db.Column(UUID(as_uuid=True), primary_key=True)
    role_id = db.Column(UUID(as_uuid=True), primary_key=True)
    deactivation_date = db.Column(
        db.DateTime(timezone=True), server_default=func.now())

    # Constructor initializing values
    def __init__(self, user_id, role_id, deactivation_date):
        self.user_id = user_id
        self.role_id = role_id
        self.deactivation_date = deactivation_date

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        return ("{'user_id':" + str(self.user_id) + ", 'role_id':"
                + str(self.role_id) + "deactivation_date:"
                + str(self.deactivation_date) + "}")
