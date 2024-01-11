from flask_restx import fields

from src.version_handler import api_version_1_web

unauthorized_response_model = api_version_1_web.model(
    "unauthorized_response_model", {"message": fields.String(example="Not authorized")}
)

internal_server_error_model = api_version_1_web.model(
    "internal_server_error_model", {
        "message": fields.String(example="Internal server error")
    }
)