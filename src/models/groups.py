from sqlalchemy import text, ForeignKey, func
from sqlalchemy.orm import relationship


from src import db
from src.models.profiles import Profiles


class Groups(db.Model):
    """
    Model for mission groups
    """

    __tablename__ = "groups"

    # Query class to handle soft deletion
    # query_class = QueryWithSoftDelete

    group_id = db.Column(
        db.String(128), server_default=text("uuid_generate_v4()"), primary_key=True
    )
    # user_id = db.Column(
    #     db.String(128), db.ForeignKey("user.user_id"), nullable=True, server_default=""
    # )
    username = db.Column(db.String(128), nullable=True)
    group_name = db.Column(db.String(128))
    notes = db.Column(db.Text())
    created_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    modified_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    # Constructor initializing values
    users = db.relationship("User", secondary="user_group", backref="groups")
    click_count = db.Column(db.Integer, default=0)  # New column for click count
    receiver_count = db.Column(db.Integer, default=0)  # New column for receiver count

    def repr_name(self):
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "username": self.username,
            "notes": self.notes,
            "click_count": self.click_count,
            "receiver_count": self.receiver_count,
            "created_at": self.created_at.strftime("%d-%m-%Y %H:%M"),
            "modified_at": self.modified_at.strftime("%d-%m-%Y %H:%M"),
        }
