from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy import text, func

from src import db
# Creating UserPermissions class that maps to table 'user_permissions'


class UserPermissions(db.Model):
    """
    Model for user_permissions table
    Attributes:
    'permission_id': Unique ID generated for each permission(UUID)
    'permission_name': Name assigned to each permission(VARCHAR(128))
    'description' : Description assigned to each permission(VARCHAR(1024))
    'created_on' : Timestamp for creation of permission(DATETIME)
    'permission_value' : Value assigned to each permission(VARCHAR(512))
    """
    __tablename__ = "user_permissions"

    permission_id = db.Column(
        db.String(128), server_default=text("uuid_generate_v4()"),
        primary_key=True, nullable=False)
    permission_name = db.Column(db.String(128))
    description = db.Column(db.String(1024))
    created_on = db.Column(db.DateTime, server_default=func.now())
    permission_value = db.Column(db.String(512))
    user_roles = relationship(
        "UserRole",
        secondary="role_permission_mapping",
        back_populates="user_permissions",
    )

    # Constructor initializing values
    def __init__(self, permission_name, description, permission_value):
        self.permission_name = permission_name
        self.description = description
        self.permission_value = permission_value

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        return ("{'permission_id':" + str(self.permission_id) +
                ", 'permission_name':" + self.permission_name + ", 'created_on':" +
                str(self.created_on) + "}")

    def repr_name(self):
        "Custom representation of the model"
        return {"permission_id": str(self.permission_id),
                "permission_name": str(self.permission_name)}
