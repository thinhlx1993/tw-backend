import os

import boto3
from botocore.config import Config
from celery.result import AsyncResult
from flask_pydantic import validate
from flask_restx import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename

from src.celery_app.tasks import chunks_files
from src.v1.data_model.common_data_model import page_parser
from src.v1.data_model.files_model import create_file_model, file_search_data_model, update_file_model
from src.v1.enums.file_upload_status import FileUploadStatus
from src.v1.services import files_services, openai_services
from src.v1.validator.files_upload_validator import (
    CreateNewFileValidator,
    UpdateFileValidator,
)
from src.v1.validator.paginator import PaginatorModel
from src.version_handler import api_version_1_web

files_ns = api_version_1_web.namespace(
    "files", description="Files Upload Functionalities"
)


class FileUploadListOperations(Resource):
    @files_ns.expect(create_file_model)
    @jwt_required
    @validate()
    def post(self, body: CreateNewFileValidator):
        """
        Create a new file APIs
        POST /user/v1/files
        """
        filename = body.filename
        status = body.status
        original_path = body.original_path
        local_path = body.local_path
        current_user = get_jwt_identity()
        file_info = files_services.create_file(
            filename, status, original_path, local_path, current_user
        )
        response_json = {"msg": "OK", "status": True, "data": file_info}
        return response_json, 200

    @files_ns.expect(page_parser)
    @jwt_required
    def get(self):
        files, total = files_services.get_files(page_parser.parse_args())
        response_json = {"msg": "OK", "status": True, "data": files, "total": total}
        return response_json, 200


class FileUploadOperations(Resource):
    @jwt_required
    @validate()
    def get(self, file_id: str):
        """
        Get file metadata by file id
        GET /user/v1/files/<file_id>
        """
        file_info, status = files_services.get_file(file_id)
        if status:
            response_json = {"msg": "OK", "status": status, "data": file_info.repr_full()}
            return response_json, 200

        response_json = {
            "msg": "File not found",
            "status": status,
            "data": {},
        }
        return response_json, 200

    @files_ns.expect(update_file_model)
    @jwt_required
    @validate()
    def put(self, file_id: str, body: UpdateFileValidator):
        """
        Update file metadata
        PUT /user/v1/files/<file_id>
        """
        file_info, status = files_services.update_file(file_id, body)
        if status:
            response_json = {"msg": "OK", "status": status, "data": file_info}
            return response_json, 200

        response_json = {"msg": "Failed to update", "status": status, "data": file_info}
        return response_json, 200

    @jwt_required
    @validate()
    def delete(self, file_id: str):
        """
        Delete file metadata
        DELETE /user/v1/files/<file_id>
        """
        status = files_services.delete_file(file_id)
        if status:
            response_json = {"msg": "OK", "status": status, "data": {}}
            return response_json, 200

        response_json = {"msg": "Failed to delete", "status": status, "data": {}}
        return response_json, 500


class FileRenderOperations(Resource):
    @jwt_required
    def post(self, file_id: str):
        """
        Create a new file APIs
        POST /user/v1/files
        """
        file_info, status = files_services.get_file(file_id)
        if not status:
            response_json = {"msg": "File not found", "status": False}
            return response_json, 500

        user_id = get_jwt_identity()
        # update file status to processing
        file_info.status = FileUploadStatus.Processing.value
        result = chunks_files.delay(file_id, user_id)
        return {"task_id": result.id}


class TaskStatusOperations(Resource):
    @jwt_required
    def get(self, file_id: str, task_id: str) -> dict[str, object]:
        """
        Check task id status
        """
        result = AsyncResult(task_id)
        return {
            "ready": result.ready(),
            "successful": result.successful(),
            "value": result.result if result.ready() else None,
        }


class FilePresignUrlOperations(Resource):
    @jwt_required
    def get(self, file_id: str):
        """
        Generate presignURL for current file_id
        Please make PUT requests to pre_signed_url with header contains x-amz-acl: public-read key value
        The pre_signed_url will be expired in 3600 min
        """
        file_info, status = files_services.get_file(file_id)
        if not status:
            response_json = {
                "msg": "File not found",
                "status": status,
                "data": {},
            }
            return response_json, 400

        pre_signed_url, original_path = files_services.generate_presign_url(file_info.filename)
        file_info.original_path = original_path
        return_data = {
            "pre_signed_url": pre_signed_url,
            "expires_in": 3600,
            "method": "PUT",
            "x-amz-acl": "public-read"
        }
        return return_data, 200


files_ns.add_resource(FileUploadListOperations, "")
files_ns.add_resource(FileUploadOperations, "/<file_id>")
files_ns.add_resource(FilePresignUrlOperations, "/<file_id>/upload")
files_ns.add_resource(FileRenderOperations, "/<file_id>/render")
files_ns.add_resource(TaskStatusOperations, "/<file_id>/tasks/<task_id>")
