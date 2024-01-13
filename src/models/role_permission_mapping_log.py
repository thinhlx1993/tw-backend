from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func

from src import db

# Creating RolePermissionMapping class that maps to role_permission_mapping table


class RolePermissionMappingLog(db.Model):
    """
    Model for role_permission_mapping table
    Attributes:
    'role_id' : Role ID(UUID)
    'permission_id': Permission ID(UUID)
    """
    __tablename__ = 'role_permission_mapping_log'

    # Table does not have Primary key(PK), but SQLAlchemy requires
    # table to have one. Hence, both have been set to PK.
    role_id = db.Column(db.String(128), primary_key=True)
    permission_id = db.Column(db.String(128), primary_key=True)
    deactivation_date = db.Column(db.DateTime(
        timezone=True), server_default=func.now())

    # Constructor initializing values
    def __init__(self, role_id, permission_id, deactivation_date):
        self.role_id = role_id
        self.permission_id = permission_id
        self.deactivation_date = deactivation_date

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.

    def __repr__(self):
        return ("{'role_id':" + str(self.role_id) + ", 'permission_id':" +
                str(self.permission_id) + "deactivation_date:" +
                str(self.deactivation_date) + "}")
