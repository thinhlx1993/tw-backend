import logging
import os

import boto3
from botocore.config import Config
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename

from src import db
from src.v1.enums.file_upload_status import FileUploadStatus
from src.v1.models.file_upload_model import FileUploadModel
from src.v1.validator.files_upload_validator import UpdateFileValidator
from src.v1.validator.paginator import PaginatorModel

# Create module log
_logger = logging.getLogger(__name__)


def get_file(file_id: str) -> (dict, bool):
    """

    Args:
        file_id: str the uuid of the file
    Returns:
        file repr_name()
        status: bool
    """
    current_file = FileUploadModel.query.filter_by(id=file_id).first()
    if not current_file:
        return {}, False
    return current_file, True


def create_file(filename, status, original_path, local_path, created_by):
    """
    Creates a new file
    :param str filename: filename
    :param str status: file status
    :param str original_path: file path on server
    :param str local_path: file path on mobile device
    :param str created_by: user who create this file
    :return FileUpload file: FileUploadModel
    """
    new_instance = FileUploadModel(
        filename, status, original_path, local_path, created_by
    )
    db.session.add(new_instance)
    db.session.flush()
    return new_instance.repr_name()


def get_files(query: PaginatorModel) -> (list, int):
    """
    Query files
    :param PaginatorModel query: page, per_page, search
    :return FileUpload files: [FileUploadModel,], total items
    """
    all_files = (
        FileUploadModel.query.filter(
            FileUploadModel.filename.ilike(f"%{query.search}%")
        )
        .order_by(FileUploadModel.created_at.desc())
        .limit(query.per_page)
        .offset(query.page * query.per_page)
        .all()
    )
    total = FileUploadModel.query.filter(
        FileUploadModel.filename.ilike(f"%{query.search}%")
    ).count()

    all_files = [file.repr_name() for file in all_files]
    return all_files, total


def update_file(file_id: str, body: UpdateFileValidator) -> (dict, bool):
    current_file = FileUploadModel.query.filter_by(id=file_id).first()
    if not current_file:
        return {}, False

    for key, value in body.model_dump().items():
        setattr(current_file, key, value)
    return current_file.repr_name(), True


def delete_file(file_id: str) -> bool:
    """
    Delete files by id
    Args:
        file_id: uuid
    Returns:
        status True or False
    """
    current_file, status = get_file(file_id)
    if not status:
        return False
    FileUploadModel.query.filter_by(id=file_id).delete()
    return True


def update_result(parent_id, full_text_result, status) -> bool:
    """
    Save meeting notes when processed
    Args:
        parent_id:
        full_text_result:
        status: failed , completed

    Returns:

    """
    current_file = FileUploadModel.query.filter_by(id=parent_id).first()
    if not current_file:
        return False
    current_file.full_text_result = full_text_result
    current_file.status = status
    db.session.commit()
    return True


def update_duration(parent_id: str, duration: int) -> bool:
    """
    Save duration
    Args:
        parent_id:
        duration:

    Returns:

    """
    current_file = FileUploadModel.query.filter_by(id=parent_id).first()
    if not current_file:
        return False
    current_file.duration = duration
    db.session.commit()
    return True


def save_meeting_note(file_id, key_points):
    """
    Save key points into database
    Args:
        file_id:
        key_points:

    Returns:
        None
    """
    file_info, status = get_file(file_id)
    if not status:
        return False

    file_info.meeting_note = key_points
    db.session.commit()
    return file_info.repr_full()


def generate_presign_url(filename: str) -> (str, str):
    """
    Generate pre signed url for the filename
    Args:
        filename: str

    Returns:
        (resigned_url, original_path)
    """
    session = boto3.session.Session()
    access_key = os.environ.get("SPACES_KEY")
    secret_key = os.environ.get("SPACES_SECRET")
    client = session.client('s3',
                            region_name='sgp1',  # Change to your region
                            endpoint_url=os.environ.get("DIGITALOCEAN_ORIGIN_ENDPOINT"),
                            # Change to your endpoint URL
                            aws_access_key_id=access_key,
                            aws_secret_access_key=secret_key,
                            config=Config(signature_version='s3v4'))

    # Name of your DigitalOcean Space and the file name you want to upload
    space_name = 'meetingx'
    user_id = get_jwt_identity()
    filename = secure_filename(filename)
    original_path = f"{user_id}/{filename}"
    # Generate a pre-signed URL for putting an object
    # please add header x-amz-acl: public-read when do the PUT request
    presigned_url = client.generate_presigned_url('put_object',
                                                  Params={
                                                      'Bucket': space_name,
                                                      'Key': original_path,
                                                      'ACL': 'public-read'
                                                  },
                                                  ExpiresIn=3600)  # URL expiry time in seconds
    return presigned_url, original_path