"""Celery tasks"""
import os
import time
import boto3
import logging
from celery import shared_task

from src.v1.enums.file_upload_status import FileUploadStatus
from src.v1.enums.user_type import UserPlan
from src.v1.services import (
    files_services,
    files_chunks_services,
    openai_services,
    user_services,
)

_logger = logging.getLogger(__name__)


@shared_task(bind=True)
def generate_user_archive(self, file_id: str) -> None:
    try:
        file_chunk, status = files_chunks_services.get_chunk_file(file_id)
        if not status:
            _logger.error(f"{file_id} not found")
            return

        file_path = file_chunk.file_path

        if not os.path.isfile(file_path):
            _logger.error(f"file not found: {file_path}")
            return

        _logger.info(f"processing file: {file_path}")
        try:
            import whisper
            import ffmpeg
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = whisper.load_model("tiny.en", device=device)
            _logger.info(f"Running on {device}")
            result = model.transcribe(file_path)
        except Exception as ex:
            result = {"text": ""}
            _logger.error("Can not decode text")

        # update file data
        file_chunk.result = result["text"]
        file_chunk.status = True
        files_chunks_services.save_changes()

        # _logger.info(result["text"])
        check_file_done.delay(file_chunk.parent_id)
        remove_file(file_path)
        _logger.info(f"{file_path} OK \n")
    except Exception as ex:
        _logger.exception(ex)
        # raise self.retry(exc=ex, countdown=5)


@shared_task()
def check_file_done(parent_id: str) -> bool:
    """
    Check all chunks are processed
    Args:
        parent_id: parent file id

    Returns:
        bool
    """
    try:
        is_completed = files_chunks_services.check_completed(parent_id)
        if is_completed:
            full_text_result = files_chunks_services.get_result(parent_id)
            status = openai_services.generate_key_points(parent_id)
            status = (
                FileUploadStatus.Completed.value
                if status
                else FileUploadStatus.Failed.value
            )
            files_services.update_result(parent_id, full_text_result, status)
            return True
        return False
    except Exception as ex:
        _logger.exception(ex)


@shared_task(bind=True)
def chunks_files(self, file_id: str, user_id: str) -> None:
    """
    Split file into multiple files
    Args:
        file_id: the file uuid
        user_id: the user who own this file
    Returns:
        None
    """
    try:
        import ffmpeg
        from ffprobe import FFProbe

        _logger.info(f"file_id {file_id}")
        upload_folder = os.environ.get("UPLOAD_FOLDER", "/tmp")
        _logger.info(f"Working folder: {upload_folder}")
        file_info, status = files_services.get_file(file_id)
        if not status:
            return
        user_info = user_services.get_user(user_id)
        subscription = user_info.get("subscription", "free")
        original_path = file_info.original_path

        # download file
        base_name = os.path.basename(original_path)
        full_base_name = start_download_file(original_path, file_id, base_name)
        metadata = FFProbe(full_base_name)
        duration_seconds = 600  # default 10 min for free user
        for stream in metadata.streams:
            if stream.duration_seconds() and (
                stream.duration_seconds() < duration_seconds
                or subscription == UserPlan.ProAccount.value
            ):
                # free user can not process long file, limit is 15 min
                duration_seconds = stream.duration_seconds()
                files_services.update_duration(file_id, stream.duration_seconds())
                break

        logging.info(
            f"full_base_name: {full_base_name} | duration_seconds: {duration_seconds}"
        )

        folder_id = f"{upload_folder}/{file_id}"
        if not os.path.isdir(folder_id):
            os.makedirs(folder_id, exist_ok=True)
            time.sleep(5)
            try:
                ffmpeg.input(full_base_name).output(
                    f"{folder_id}/segment_%d.mp3",
                    t=duration_seconds,
                    f="segment",
                    segment_time="30",
                ).run()
            except Exception as ex:
                _logger.error(f"Process file error: {original_path}")
                remove_file(full_base_name)
                return
        else:
            is_done = check_file_done.delay(file_id)
            if is_done:
                remove_file(full_base_name)
                return

        processed_list = []
        for file in os.listdir(folder_id):
            if not file.endswith("mp3"):
                continue
            file_path = f"{folder_id}/{file}"
            chunk_file, status = files_chunks_services.check_exist(file_path)
            if not status:
                chunk_file = files_chunks_services.create_file(
                    parent_id=file_id, file_path=file_path, status=False
                )
                files_chunks_services.save_changes()

            # start generate data
            if chunk_file and chunk_file.status == False:
                processed_list.append(chunk_file.id)
            else:
                _logger.info(
                    f"file {file_path} is already processed {chunk_file.status}"
                )
        for chunk_file_id in processed_list:
            generate_user_archive.delay(chunk_file_id)

        remove_file(full_base_name)
    except Exception as ex:
        files_chunks_services.rollback()
        _logger.exception(ex)
        # raise self.retry(exc=ex, countdown=5)


def start_download_file(original_path, file_id, base_name):
    _logger.info(f"start download {original_path} | {file_id} | {base_name}")
    # Initialize a session using DigitalOcean Spaces
    s3 = boto3.client(
        "s3",
        region_name=os.environ.get("REGION_NAME"),  # or your region
        endpoint_url=os.environ.get("DIGITALOCEAN_ORIGIN_ENDPOINT"),  # or your endpoint
        aws_access_key_id=os.environ.get("SPACES_KEY"),
        aws_secret_access_key=os.environ.get("SPACES_SECRET"),
    )

    # Your bucket name and file name
    bucket_name = os.environ.get("BUCKET_NAME")

    # Get the file
    upload_folder = os.environ.get("UPLOAD_FOLDER", "/tmp")
    os.makedirs(upload_folder, exist_ok=True)
    file_to_save = f"{upload_folder}/{base_name}"
    if not os.path.isfile(file_to_save):
        s3.download_file(bucket_name, f"{original_path}", file_to_save)
    return file_to_save


def remove_file(file_path):
    try:
        os.remove(file_path)
    except Exception as ex:
        _logger.exception(ex)
