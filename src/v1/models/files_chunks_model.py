import json
from src import db

from sqlalchemy.orm import relationship
from sqlalchemy import func, text, ForeignKey
from sqlalchemy.dialects.postgresql import BYTEA


class FileChunksModel(db.Model):
    """
    Model for file_chunks table
    Attributes:
    'id =': Unique ID generated for each permission(UUID)
    'filename': filename(VARCHAR(128))
    'result' : Description assigned to each permission(VARCHAR(1024))
    'created_at' : Timestamp for creation of permission(DATETIME)
    """

    __tablename__ = "file_chunks"

    id = db.Column(
        db.String(128),
        server_default=text("uuid_generate_v4()"),
        primary_key=True,
        nullable=False,
    )
    created_at = db.Column(db.DateTime, server_default=func.now())
    status = db.Column(db.Boolean, server_default="false")
    file_path = db.Column(db.String(1024))
    duration = db.Column(db.Integer)
    result = db.Column(db.Text)
    parent_id = db.Column(
        db.String(128),
        ForeignKey("file_upload.id"),
        nullable=False,
        comment="the main file, chunks are split using this file",
    )

    # Constructor initializing values
    def __init__(self, parent_id, file_path, status):
        self.parent_id = parent_id
        self.file_path = file_path
        self.status = status

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        return str(
            {
                "id": self.id,
                "parent_id": self.parent_id,
                "file_path": self.file_path,
                "status": self.status,
                "created_at": self.created_at.isoformat(),
            }
        )

    def repr_name(self):
        return {
            "id": self.id,
            "parent_id": self.parent_id,
            "file_path": self.file_path,
            "status": self.status,
            "result": self.result,
            "created_at": self.created_at.isoformat(),
        }
