from typing import Optional
from pydantic import BaseModel, Field

from src.v1.enums.file_upload_status import FileUploadStatus, AllowExtEnum

"""
class MyPydanticModel(BaseModel):
    title: Optional[str] = Field(None, max_length=10)

class MyPydanticModel(BaseModel):
    title: str = Field(..., max_length=10)

"""


class GeneratePresignURL(BaseModel):
    filename: str = Field(..., max_length=2048)


class CreateNewFileValidator(BaseModel):
    filename: str = Field(..., max_length=2048)
    status: FileUploadStatus = Field(..., max_length=128)
    original_path: Optional[str] = Field(None, max_length=1024)
    local_path: Optional[str] = Field(None, max_length=1024)


class UpdateFileValidator(BaseModel):
    """
    filename = db.Column(db.String(2048))
    description = db.Column(db.String(1024))
    created_at = db.Column(db.DateTime, server_default=func.now())
    status = db.Column(db.String(128), nullable=False)
    local_path = db.Column(db.String(1024))
    speech_path = db.Column(db.String(1024))
    original_path = db.Column(db.String(1024))
    duration = db.Column(db.Integer)
    meeting_note = db.Column(db.Text)
    """

    filename: Optional[str] = Field(None, max_length=2048)
    description: Optional[str] = Field(None, max_length=1024)
    status: Optional[FileUploadStatus] = Field(None, max_length=128)
    local_path: Optional[str] = Field(None, max_length=1024)
    speech_path: Optional[str] = Field(None, max_length=1024)
    original_path: Optional[str] = Field(None, max_length=1024)
    duration: Optional[int] = None
    meeting_note: Optional[str] = None


def allowed_file(filename):
    return (
        "." in filename and filename.rsplit(".", 1)[1].lower() in AllowExtEnum.Ext.value
    )
