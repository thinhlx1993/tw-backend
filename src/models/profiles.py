from sqlalchemy import text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship


from src import db
from src.query.query_with_soft_delete import QueryWithSoftDelete


class Profiles(db.Model):
    """
    Model for Profiles
    """
    __tablename__ = "profiles"

    profile_id = db.Column(
        db.String(128),
        server_default=text("uuid_generate_v4()"),
        primary_key=True
    )
    group_id = db.Column(
        db.String(128),
        ForeignKey("groups.group_id"),
        nullable=False)
    username = db.Column(db.String(128), nullable=True)
    name = db.Column(db.String(128), nullable=True)
    password = db.Column(db.String(128), nullable=True)
    fa = db.Column(db.String(128), nullable=True)
    proxy = db.Column(db.String(128), nullable=True)
    gpt_key = db.Column(db.String(128), nullable=True)
    cookies = db.Column(db.String(128), nullable=True)
    notes = db.Column(db.Text(), nullable=True)
    metadata = db.Column(db.JSON(), nullable=True)
    status = db.Column(db.String(128), nullable=True)
    created_at = db.Column(
        db.DateTime(),
        nullable=False,
        server_default=func.now()
    )
    modified_at = db.Column(
        db.DateTime(),
        nullable=False,
        server_default=func.now()
    )

    # Constructor initializing values
    def __init__(self, username, password,
                 fa, proxy, gpt_key, cookies,
                 notes, status):
        self.username = username
        self.password = password
        self.fa = fa
        self.proxy = proxy
        self.gpt_key = gpt_key
        self.cookies = cookies
        self.notes = notes
        self.status = status

    def repr_name(self):
        return {
            "profile_id": self.profile_id,
            "group_id": self.group_id,
            "username": self.username,
            "password": self.password,
            "fa": self.fa,
            "proxy": self.proxy,
            "gpt_key": self.gpt_key,
            "cookies": self.cookies,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat()
        }
