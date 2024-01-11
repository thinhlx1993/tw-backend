import json
from src import db

from sqlalchemy.orm import relationship
from sqlalchemy import func, text, ForeignKey
from sqlalchemy.dialects.postgresql import BYTEA


class FileUploadModel(db.Model):
    """
    Model for file_upload table
    Attributes:
    'id =': Unique ID generated for each permission(UUID)
    'filename': filename(VARCHAR(128))
    'description' : Description assigned to each permission(VARCHAR(1024))
    'created_at' : Timestamp for creation of permission(DATETIME)
    """

    __tablename__ = "file_upload"

    id = db.Column(
        db.String(128),
        server_default=text("uuid_generate_v4()"),
        primary_key=True,
        nullable=False,
    )
    filename = db.Column(db.String(2048))
    description = db.Column(db.String(1024))
    created_at = db.Column(db.DateTime, server_default=func.now())
    created_by = db.Column(
        db.String(128),
        ForeignKey("users.user_id"),
        nullable=True,
        comment="the user who create this file"
    )
    status = db.Column(db.String(128), nullable=False)
    local_path = db.Column(db.String(1024))
    speech_path = db.Column(db.String(1024))
    original_path = db.Column(db.String(1024))
    duration = db.Column(db.Integer)
    meeting_note = db.Column(db.Text)
    full_text_result = db.Column(db.Text)

    chunks = relationship("FileChunksModel", backref="file_upload")
    user = relationship("User", backref="user")

    # Constructor initializing values
    def __init__(self, filename, status, original_path, local_path, created_by):
        self.filename = filename
        self.status = status
        self.original_path = original_path
        self.local_path = local_path
        self.created_by = created_by

    # String representation of the model. Can be edited to show whatever
    # attributes we want to see.
    def __repr__(self):
        return str(
            {
                "id": self.id,
                "filename": self.filename,
                "status": self.status,
                "created_at": self.created_at.isoformat()
            }
        )

    def repr_name(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "local_path": self.local_path,
            "speech_path": self.speech_path,
            "original_path": self.original_path,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }

    def repr_full(self):
        return {
            "id": self.id,
            "filename": self.filename,
            "local_path": self.local_path,
            "speech_path": self.speech_path,
            "original_path": self.original_path,
            "duration": self.duration,
            "meeting_note": self.meeting_note,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "created_by": self.user.user_info()
        }
