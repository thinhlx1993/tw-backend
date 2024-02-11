from src import db
from sqlalchemy import text, ForeignKey, func


class Profiles(db.Model):
    """
    Model for Profiles
    """

    __tablename__ = "profiles"

    profile_id = db.Column(
        db.String(128), server_default=text("uuid_generate_v4()"), primary_key=True
    )
    group_id = db.Column(db.String(128), ForeignKey("groups.group_id"), nullable=True)
    username = db.Column(db.String(128), nullable=True, unique=True, server_default="")
    user_access = db.Column(
        db.String(128), nullable=True, unique=False, server_default=""
    )
    name = db.Column(db.String(128), nullable=True, server_default="")
    password = db.Column(db.String(128), nullable=True, server_default="")
    fa = db.Column(db.String(128), nullable=True, server_default="")
    proxy = db.Column(db.String(128), nullable=True, server_default="")
    gpt_key = db.Column(db.String(128), nullable=True, server_default="")
    cookies = db.Column(db.String(128), nullable=True, server_default="")
    notes = db.Column(db.Text(), nullable=True, server_default="")
    profile_data = db.Column(db.JSON(), nullable=True)
    browser_data = db.Column(db.Text(), nullable=True, server_default="")
    status = db.Column(db.String(128), nullable=True, server_default="")
    created_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    modified_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    hma_profile_id = db.Column(db.String(128), nullable=True, server_default="")
    emails = db.Column(db.String(128), nullable=True, server_default="")
    pass_emails = db.Column(db.String(128), nullable=True, server_default="")
    phone_number = db.Column(db.String(128), nullable=True, server_default="")
    debugger_port = db.Column(db.String(128), nullable=True)
    owner = db.Column(db.String(128), nullable=True, unique=False, server_default="")
    main_profile = db.Column(db.Boolean, server_default="false", nullable=True)
    click_count = db.Column(db.Integer, nullable=True)
    comment_count = db.Column(db.Integer, nullable=True)
    like_count = db.Column(db.Integer, nullable=True)
    is_disable = db.Column(db.Boolean, server_default="false", nullable=True)
    interactions_giver = db.relationship(
        "Events", foreign_keys="Events.profile_id", backref="receiver", lazy=True
    )
    interactions_interact = db.relationship(
        "Events",
        foreign_keys="Events.profile_id_interact",
        backref="giver",
        lazy=True,
    )

    def repr_name(self):
        return {
            "profile_id": self.profile_id,
            "group_id": self.group_id,
            "owner": self.owner,
            "username": self.username if self.username else "",
            "user_access": self.user_access if self.user_access else "",
            "password": self.password if self.password else "",
            "fa": self.fa if self.fa else "",
            "proxy": self.proxy if self.proxy else "",
            "gpt_key": self.gpt_key if self.gpt_key else "",
            "cookies": self.cookies if self.cookies else "",
            "hma_profile_id": self.hma_profile_id if self.hma_profile_id else "",
            "emails": self.emails if self.emails else "",
            "status": self.status if self.status else "",
            "debugger_port": self.debugger_port,
            "main_profile": self.main_profile,
            "pass_emails": self.pass_emails if self.pass_emails else "",
            "phone_number": self.phone_number if self.phone_number else "",
            "notes": self.notes if self.notes else "",
            "profile_data": self.profile_data,
            "created_at": self.created_at.strftime("%d-%m-%Y %H:%M"),
            "modified_at": self.modified_at.strftime("%d-%m-%Y %H:%M"),
        }

    def event_data(self):
        return {"username": self.username if self.username else ""}
