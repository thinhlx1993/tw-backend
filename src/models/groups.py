from sqlalchemy import text, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship


from src import db
from src.query.query_with_soft_delete import QueryWithSoftDelete

class Groups(db.Model):
    """
    Model for mission groups
    """
    __tablename__ = "groups"

    # Query class to handle soft deletion
    # query_class = QueryWithSoftDelete

    group_id = db.Column(
        db.String(128),
        server_default=text(
        "uuid_generate_v4()"),
        primary_key=True
    )
    group_name = db.Column(db.String(128))
    notes = db.Column(db.Text())
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
    def __init__(self, group_name, notes):
        self.group_name = group_name
        self.notes = notes

    def repr_name(self):
        return {
            "group_id": self.group_id,
            "group_name": self.group_name,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat()
        }
