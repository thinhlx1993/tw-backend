from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey, UniqueConstraint

from src import db
# Creating RolePermissionMapping class that maps to role_permission_mapping table


class RolePermissionMapping(db.Model):
    """
    Model for role_permission_mapping table
    Attributes:
    'role_id' : Role ID(UUID)
    'permission_id': Permission ID(UUID)
    """
    __tablename__ = 'role_permission_mapping'

    # Table does not have Primary key(PK), but SQLAlchemy requires
    # table to have one. Hence, both have been set to PK.
    role_id = db.Column(db.String(128),
                        ForeignKey("user_role.role_id"), primary_key=True)
    permission_id = db.Column(
        db.String(128), ForeignKey("user_permissions.permission_id"), primary_key=True)
    __table_args__ = (UniqueConstraint('role_id',
                                       'permission_id', name='_role_permission_uc'),)

    # Constructor initializing values
    def __init__(self, role_id, permission_id):
        self.role_id = role_id
        self.permission_id = permission_id

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        return ("{'role_id':" + str(self.role_id) + ", 'permission_id':" +
                str(self.permission_id) + "}")
