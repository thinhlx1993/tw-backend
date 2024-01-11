import json
from src import db

from sqlalchemy.orm import relationship
from sqlalchemy import func, text
from sqlalchemy.dialects.postgresql import BYTEA

# mapping tables
UserGroup = db.Table(
    "user_group",
    db.Model.metadata,
    db.Column(
        "id",
        db.String(128),
        server_default=text("uuid_generate_v4()"),
        primary_key=True,
        nullable=False,
    ),
    db.Column("user_id", db.String(128), db.ForeignKey("users.user_id")),
    db.Column("group_id", db.String(128), db.ForeignKey("groups.id")),
)

UserRole = db.Table(
    "user_role",
    db.Model.metadata,
    db.Column(
        "id",
        db.String(128),
        server_default=text("uuid_generate_v4()"),
        primary_key=True,
        nullable=False,
    ),
    db.Column("user_id", db.String(128), db.ForeignKey("users.user_id")),
    db.Column("role_id", db.String(128), db.ForeignKey("roles.id")),
)


class Group(db.Model):
    """
    Model for groups table
    Attributes:
    'id =': Unique ID generated for each permission(UUID)
    'name': Name assigned to each permission(VARCHAR(128))
    'description' : Description assigned to each permission(VARCHAR(1024))
    'created_on' : Timestamp for creation of permission(DATETIME)
    'is_deletable' : Be able to delete
    """

    __tablename__ = "groups"

    id = db.Column(
        db.String(128),
        server_default=text("uuid_generate_v4()"),
        primary_key=True,
        nullable=False,
    )
    name = db.Column(db.String(128))
    description = db.Column(db.String(1024))
    created_on = db.Column(db.DateTime, server_default=func.now())
    is_deletable = db.Column(db.Boolean, server_default="false")

    # Constructor initializing values
    def __init__(self, name, description, is_deletable):
        self.name = name
        self.description = description
        self.is_deletable = is_deletable

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        return str(
            {
                "id": self.id,
                "name": self.name,
                "description": self.description,
                "created_on": self.created_on.isoformat(),
                "is_deletable": self.is_deletable,
            }
        )

    def repr_name(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_on": self.created_on.isoformat(),
            "is_deletable": self.is_deletable,
        }


class Role(db.Model):
    """Model for roles table.

    Attributes:
    'id': Unique ID generated for each role(UUID)
    'name': Name assigned to each role(VARCHAR(32))
    'description': Description assigned to each role(VARCHAR(1024))
    'created_on': Timestamp for creation of role(DATETIME)
    'is_deletable': Be able to delete or not
    """

    __tablename__ = "roles"

    id = db.Column(
        db.String(128),
        server_default=text("uuid_generate_v4()"),
        primary_key=True,
        nullable=False,
    )
    name = db.Column(db.String(32))
    description = db.Column(db.String(1024))
    created_on = db.Column(db.DateTime, server_default=func.now())
    is_deletable = db.Column(db.Boolean, server_default="false")

    # Constructor initializing values

    def __init__(self, role_name, role_description, is_deletable):
        self.role_name = role_name
        self.role_description = role_description
        self.is_deletable = is_deletable

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        return str(
            {
                "id": str(self.id),
                "name": self.name,
                "description": self.description,
                "created_on": self.created_on.isoformat(),
                "is_deletable": self.is_deletable,
            }
        )

    def repr_name(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_on": self.created_on.isoformat(),
            "is_deletable": self.is_deletable,
        }


class User(db.Model):
    """
    Model for user Table
    Attributes:
    'user_id' : Unique ID generated for each user(UUID)
    'username' : Registered Username of user(VARCHAR(256))
    'email' : Registered email address of user(VARCHAR(256))
    'password' : Encrypted password of user(VARCHAR(256))
    'first_name' : First name of user(VARCHAR(128))
    'last_name' : Last name of user(VARCHAR(128))
    'created_at' : Timestamp for creation of user(DATETIME)
    'is_disabled' : Boolean check if user is disabled(BOOLEAN)
    'mfa_enabled' : Boolean check if user has multifactor auth enabled(BOOLEAN)
    'phone_number' : Phone number of user(VARCHAR(128))
    'is_email_verified' : Boolean check if user email is verified disabled(BOOLEAN)
    """

    __tablename__ = "users"

    user_id = db.Column(
        db.String(128),
        server_default=text("uuid_generate_v4()"),
        primary_key=True,
        nullable=False,
    )
    username = db.Column(db.String(256), nullable=True, unique=True)
    email = db.Column(db.String(256), nullable=False, unique=True)
    password = db.Column(db.String(512))
    first_name = db.Column(db.String(128))
    last_name = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, server_default=func.now())
    code_generated_at = db.Column(db.DateTime, server_default=func.now())
    last_activate_at = db.Column(db.DateTime, server_default=func.now())
    is_disabled = db.Column(db.Boolean, server_default="false")
    mfa_enabled = db.Column(db.Boolean, server_default="false")
    mfa_secret = db.Column(BYTEA)
    phone_number = db.Column(db.String(128))
    is_email_verified = db.Column(db.Boolean, server_default="false")
    language = db.Column(db.String(128), server_default="english")
    subscription = db.Column(db.String(128), server_default="free")
    password_reset_tokens = relationship("UserPasswordResetToken", backref="users")
    roles = relationship("Role", secondary=UserRole)
    groups = relationship("Group", secondary=UserGroup)

    # Constructor initializing values.
    def __init__(self, email):
        self.email = email

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        """
        String representation for results fetched from the table
        """
        return str(
            {
                "user_id": str(self.user_id),
                "username": str(self.username),
                "email": str(self.email),
                "first_name": str(self.first_name),
                "last_name": str(self.last_name),
                "created_at": str(self.created_at),
                "is_disabled": str(self.is_disabled),
                "phone_number": str(self.phone_number),
                "is_email_verified": self.is_email_verified,
            }
        )

    def repr_name(self):
        """dict representation of user row"""
        return {
            "user_id": str(self.user_id),
            "username": str(self.username),
            "email": str(self.email),
            "first_name": str(self.first_name),
            "last_name": str(self.last_name),
            "created_at": str(self.created_at),
            "is_disabled": str(self.is_disabled),
            "phone_number": str(self.phone_number),
            "is_email_verified": self.is_email_verified,
            "roles": [role.repr_name() for role in self.roles],
            "groups": [group.repr_name() for group in self.groups],
        }

    def user_info(self):
        """dict representation of user user_info"""
        return {
            "user_id": self.user_id,
            "email": self.email,
            "language": self.language if self.language else 'english',
            "subscription": self.subscription
        }
