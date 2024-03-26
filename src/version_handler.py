from flask import Blueprint
from flask_restx import Api

authorizations = {
    "Bearer Auth": {"type": "apiKey", "in": "header", "name": "Authorization"},
}

agent_authorizations = {
    "Basic Auth": {"type": "basic", "in": "header", "name": "Authorization"}
}

version_1_web = Blueprint("version_1_web", __name__)
api_version_1_web = Api(
    version_1_web, authorizations=authorizations, security="Bearer Auth"
)
