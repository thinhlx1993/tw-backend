"""Controller for teams."""

import logging
from datetime import datetime
import json, uuid, os
from concurrent.futures import ThreadPoolExecutor

from flask_restx import fields, reqparse, Resource
from flask_jwt_extended import get_jwt_claims
from flask_jwt_extended import get_jwt_identity
from flask import current_app
from sentry_sdk import capture_exception

from src.models import teams
from src.parsers import page_parser
from src.services import user_services, teams_services, profiles_services
from src.services import migration_services
from src.utilities.custom_decorator import custom_jwt_required
from src.version_handler import api_version_1_web
from src.custom_exceptions import InvalidJWTToken
from src.enums.role_permissions import RoleId

# Create module log
_logger = logging.getLogger(__name__)

# Org fetch parser

profiles_ns2 = api_version_1_web.namespace(
    'profiles',
    description='Profiles Functionalities')


# username, password, fa, proxy, gpt_key, cookies, notes, status
profile_create_model = profiles_ns2.model(
    "profile_create_model", {
        "username": fields.String(example="username"),
        "password": fields.String(example="password"),
        "fa": fields.String(example="fa"),
        "proxy": fields.String(example="proxy"),
        "gpt_key": fields.String(example="gpt_key"),
        "cookies": fields.String(example="cookies"),
        "notes": fields.String(example="notes"),
        "status": fields.String(example="status")
    }
)

# Internal error response model
internal_server_error_model = profiles_ns2.model(
    "internal_server_error_model", {
        "message": fields.String(example="Internal server error")
    }
)

# Unauthorized response model
unauthorized_response_model = profiles_ns2.model(
    "unauthorized_response_model", {
        "message": fields.String(example="Not authorized")
    }
)


class ProfilesController(Resource):
    """Class for / functionalities."""

    # @profiles_ns2.response(200, "OK", org_fetch_response_ok_model)
    # @profiles_ns2.response(400, "Bad Request", bad_response_model)
    @profiles_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @profiles_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def get(self):
        """Used to retrieve list of profiles"""
        profiles = profiles_services.get_all_profiles()
        return profiles, 200

    @profiles_ns2.expect(profile_create_model)
    # @org_ns2.response(200, "OK", org_create_response_ok_model)
    # @org_ns2.response(400, "Bad Request", org_create_bad_response_model)
    @profiles_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @profiles_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def post(self):
        """Used to create teams"""
        try:
            data = profiles_ns2.payload
            user_claims = get_jwt_claims()
            user_id = user_claims['user_id']
            teams_id = user_claims['teams_id']
            migration_services.set_search_path(teams_id)
        except Exception as e:
            _logger.debug(f"Data not valid: {e}")
            return {"message": "Data not valid"}, 400
        profile = profiles_services.create_profile(data)
        return {"profile_id": profile.profile_id}, 200


profiles_ns2.add_resource(ProfilesController, "/")
