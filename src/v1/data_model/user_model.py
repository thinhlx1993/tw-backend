import uuid
from flask_restx import fields
from src.version_handler import api_version_1_web

user_getcode_data = {
    "email": fields.String(example="thinhle.ict@gmail.com", required=True),
}
user_login_data = {
    "email": fields.String(example="thinhle.ict@gmail.com", required=True),
    "code": fields.String(example="123456", required=True),
}

user_login_model = api_version_1_web.model("user_login_model", user_login_data)

user_getcode_model = api_version_1_web.model("user_getcode_model", user_getcode_data)
