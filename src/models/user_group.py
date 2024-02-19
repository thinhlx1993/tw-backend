from src import db


class UserGroup(db.Model):
    """
    Association table for user-group relationship
    """

    __tablename__ = "user_group"

    user_id = db.Column(db.String(128), db.ForeignKey("user.user_id"), primary_key=True)
    group_id = db.Column(
        db.String(128), db.ForeignKey("groups.group_id"), primary_key=True
    )
