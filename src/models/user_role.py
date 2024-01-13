"""Model for UserRole table."""

from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src import db
# Creating UserRole class that maps to user_role table


class UserRole(db.Model):
    """Model for user_role table.

    Attributes:
    'role_id': Unique ID generated for each role(UUID)
    'role_name': Name assigned to each role(VARCHAR(32))
    'role_description': Description assigned to each role(VARCHAR(1024))
    'created_on': Timestamp for creation of role(DATETIME)
    """
    __tablename__ = 'user_role'

    role_id = db.Column(db.String(128),
                        server_default=text("uuid_generate_v4()"),
                        primary_key=True, nullable=False)
    role_name = db.Column(db.String(32))
    role_description = db.Column(db.String(1024))
    created_on = db.Column(db.DateTime, server_default=func.now())
    is_deletable = db.Column(db.Boolean)
    user_permissions = relationship(
        "UserPermissions",
        secondary="role_permission_mapping",
        back_populates="user_roles",
    )
    users = relationship(
        "User", secondary="user_role_mapping", back_populates="user_roles"
    )
    # Constructor initializing values

    def __init__(
            self, role_name, role_description, is_deletable):
        self.role_name = role_name
        self.role_description = role_description
        self.is_deletable = is_deletable

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        return str({
            "role_id": str(self.role_id),
            "role_name": self.role_name,
            "role_description": self.role_description,
            "created_on": str(self.created_on),
            "is_deletable": str(self.is_deletable)
        })

    def repr_name(self):
        "Custom representation of the model."
        return {
            "role_id": str(self.role_id),
            "role_name": str(self.role_name)
        }
