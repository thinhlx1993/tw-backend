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
        db.String(128), server_default=text("uuid_generate_v4()"), primary_key=True
    )
    group_id = db.Column(db.String(128), ForeignKey("groups.group_id"), nullable=True)
    username = db.Column(db.String(128), nullable=True, unique=True)
    name = db.Column(db.String(128), nullable=True)
    password = db.Column(db.String(128), nullable=True)
    fa = db.Column(db.String(128), nullable=True)
    proxy = db.Column(db.String(128), nullable=True)
    gpt_key = db.Column(db.String(128), nullable=True)
    cookies = db.Column(db.String(128), nullable=True)
    notes = db.Column(db.Text(), nullable=True)
    profile_data = db.Column(db.JSON(), nullable=True)
    browser_data = db.Column(db.Text(), nullable=True)
    status = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    modified_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    hma_profile_id = db.Column(db.String(128), nullable=True)
    emails = db.Column(db.String(128), nullable=True)
    pass_emails = db.Column(db.String(128), nullable=True)
    phone_number = db.Column(db.String(128), nullable=True)

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
            "hma_profile_id": self.hma_profile_id,
            "emails": self.emails,
            "pass_emails": self.pass_emails,
            "phone_number": self.phone_number,
            "notes": self.notes,
            "created_at": self.created_at.strftime("%d-%m-%Y %H:%M"),
            "modified_at": self.modified_at.strftime("%d-%m-%Y %H:%M"),
            "group": self.group.repr_name() if self.group else None,
        }
