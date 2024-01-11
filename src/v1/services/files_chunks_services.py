import os
import logging
from datetime import datetime

from src import db
from src.v1.models import FileChunksModel

# Create module log
_logger = logging.getLogger(__name__)


def save_changes() -> bool:
    db.session.commit()
    return True


def get_chunk_file(file_id: str) -> (dict, bool):
    """

    Args:
        file_id: str the uuid of the file
    Returns:
        file repr_name()
        status: bool
    """
    current_file = FileChunksModel.query.filter_by(id=file_id).first()
    if not current_file:
        return None, False
    return current_file, True


def check_exist(file_path: str) -> (dict, bool):
    """

    Args:
        file_path: str the uuid of the file
    Returns:
        file repr_name()
        status: bool
    """
    current_file = FileChunksModel.query.filter_by(file_path=file_path).first()
    if not current_file:
        return None, False
    return current_file, True


def create_file(parent_id, file_path, status=False):
    """
    Creates a new file
    :param str parent_id: parent
    :param str file_path: file_path
    :param bool status: status
    :return FileChunksModel file: FileChunksModel
    """
    new_instance = FileChunksModel(
        parent_id=parent_id, file_path=file_path, status=status
    )
    db.session.add(new_instance)
    db.session.flush()
    return new_instance


def check_completed(parent_id) -> bool:
    """
    Check if all files are processed
    Args:
        parent_id:

    Returns:
        bool
    """
    remaining = FileChunksModel.query.filter_by(parent_id=parent_id, status=False).first()
    return True if not remaining else False


def get_result(parent_id: str) -> str:
    """
    Read all chunks and concat into single file
    Args:
        parent_id: 

    Returns:
        speech to text result
    """
    chunks = FileChunksModel.query.filter_by(parent_id=parent_id).all()
    results = [""]*len(chunks)
    for chunk in chunks:
        # example file_path
        # uploads/a2a2bb82-daf9-4a63-93a8-e3fa533ce198/segment_0.mp3
        file_path = chunk.file_path
        result = chunk.result
        basename = os.path.basename(file_path)
        file_name, file_ext = os.path.splitext(basename)
        _, idx = file_name.split("_")
        results[int(idx)] = result
    return " ".join(results)


def rollback() -> bool:
    db.session.rollback()
    return True
