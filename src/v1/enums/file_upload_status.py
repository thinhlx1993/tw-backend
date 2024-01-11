from enum import Enum


class FileUploadStatus(str, Enum):
    """User type for File Upload"""
    Processing = "processing"
    Recording = "recording"
    Uploading = "uploading"
    Completed = "processed"
    Failed = "failed"
    Added = "added"


class AllowExtEnum(Enum):
    Ext = {'mp3', 'mp4', 'mov', 'mpeg'}
