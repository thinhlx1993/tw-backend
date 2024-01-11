import os
import logging
import uuid

import boto3
import requests
from botocore.exceptions import ClientError
from botocore.client import Config

from flask import Flask, flash, request, redirect, url_for
from flask_pydantic import validate
from flask_restx import Resource, reqparse, fields
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename

from src.v1.data_model.common_data_model import page_parser
from src.v1.data_model.files_model import (
    create_file_model,
    file_search_data_model,
    update_file_model,
)
from src.v1.services import files_services
from src.v1.validator.files_upload_validator import (
    CreateNewFileValidator,
    UpdateFileValidator,
    allowed_file, GeneratePresignURL,
)
from src.v1.validator.paginator import PaginatorModel
from src.version_handler import api_version_1_web

upload_files_ns = api_version_1_web.namespace(
    "uploads", description="Upload Functionalities"
)

upload_body = {
    "filename": fields.String(example="filename.mp4", required=True)
}

upload_body_model = api_version_1_web.model("upload_body_model", upload_body)


class FileBinUploadOperations(Resource):
    # @upload_files_ns.expect(upload_parser)
    # def post(self):
    #     """
    #     Create a new file APIs
    #     POST /user/v1/files
    #     """
    #     # check if the post request has the file part
    #     args = upload_parser.parse_args()
    #     # if "file" not in request.files:
    #     #     flash("No file part")
    #     #     return redirect(request.url)
    #
    #     file = args["file"]  # This is FileStorage instance
    #     # If the user does not select a file, the browser submits an
    #     # empty file without a filename.
    #     if file.filename == "":
    #         flash("No selected file")
    #         return redirect(request.url)
    #     if file and allowed_file(file.filename):
    #         filename = secure_filename(file.filename)
    #         os.makedirs(os.environ.get("UPLOAD_FOLDER", "uploads"), exist_ok=True)
    #         file.save(
    #             os.path.join(os.environ.get("UPLOAD_FOLDER", "uploads"), filename)
    #         )
    #         return (
    #             os.path.join(os.environ.get("UPLOAD_FOLDER", "uploads"), filename),
    #             200,
    #         )
    #     return "upload failed", 500

    @upload_files_ns.expect(upload_body_model)
    @validate()
    @jwt_required
    def post(self, body: GeneratePresignURL):
        """
        Generate a presigned URL S3 POST request to upload a file
        Args:
            body:
                filename
        Returns:
            presigned URL
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
        filename = secure_filename(body.filename)
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
        return_data = {
            "pregisned_url": presigned_url,
            "original_path": original_path,
            "filename": filename
        }
        return return_data, 200


# upload_files_ns.add_resource(FileBinUploadOperations, "")
