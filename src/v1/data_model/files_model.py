import uuid
from flask_restx import fields, reqparse
from src.version_handler import api_version_1_web

file_create_data = {
    "filename": fields.String(example="Input your file name", required=True),
    "status": fields.String(example="added", required=True),
    "original_path": fields.String(example="file path that upload api return", required=False),
    "local_path": fields.String(example="file path in mobile device", required=False)

}

file_update_data = {
    "filename": fields.String(example="New filename", required=False),
    "description": fields.String(example="description", required=False),
    "status": fields.String(example="uploading", required=False),
    "local_path": fields.String(example="file path", required=False),
    "speech_path": fields.String(example="speech file path", required=False),
    "original_path": fields.String(example="the original file path", required=False)
}


file_search_data = {
    "page": fields.String(example=0, required=False, location='args'),
    "per_page": fields.String(example=10, required=False, location='args'),
    "search": fields.String(example="filename", required=False, location='args'),
}


create_file_model = api_version_1_web.model("create_file_model", file_create_data)
file_search_data_model = api_version_1_web.model("file_search_data_model", file_search_data)
update_file_model = api_version_1_web.model("update_file_model", file_update_data)