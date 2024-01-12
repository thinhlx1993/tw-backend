"""Controller for profiles."""

import logging
from flask_restx import fields, Resource
from flask_jwt_extended import get_jwt_claims
from src.services import profiles_services
from src.services import migration_services
from src.utilities.custom_decorator import custom_jwt_required
from src.version_handler import api_version_1_web

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

profile_update_model = profiles_ns2.model(
    "profile_update_model", {
        "username": fields.String(example="new_username"),
        "password": fields.String(example="new_password"),
        "fa": fields.String(example="new_fa"),
        "proxy": fields.String(example="new_proxy"),
        "gpt_key": fields.String(example="new_gpt_key"),
        "cookies": fields.String(example="new_cookies"),
        "notes": fields.String(example="new_notes"),
        "status": fields.String(example="new_status")
    }
)

profile_operation_response_model = profiles_ns2.model(
    "profile_operation_response_model", {
        "message": fields.String(example="Operation successful"),
        "profile": fields.Nested(profile_update_model, description="Profile details")
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


class ProfilesIdController(Resource):
    """Class for /profiles/profile_id functionalities."""
    @profiles_ns2.expect(profile_update_model)  # Assuming profile_update_model is defined for updating a profile
    @profiles_ns2.response(200, "Profile updated successfully", profile_operation_response_model)
    @profiles_ns2.response(401, "Authorization information is missing or invalid.", unauthorized_response_model)
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def put(self, profile_id):
        """Update a profile by ID"""
        try:
            data = profiles_ns2.payload
            profile = profiles_services.update_profile(profile_id, data)
            if profile:
                return {"message": "Profile updated successfully", "profile": profile}, 200
            return {"message": "Profile not found"}, 404
        except Exception as e:
            _logger.debug(f"Error updating profile: {e}")
            return {"message": "Data not valid or internal error"}, 400

    @profiles_ns2.response(200, "Profile deleted successfully", profile_operation_response_model)
    @profiles_ns2.response(401, "Authorization information is missing or invalid.", unauthorized_response_model)
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def delete(self, profile_id):
        """Delete a profile by ID"""
        try:
            result = profiles_services.delete_profile(profile_id)
            if result:
                return {"message": "Profile deleted successfully"}, 200
            return {"message": "Profile not found"}, 404
        except Exception as e:
            _logger.debug(f"Error deleting profile: {e}")
            return {"message": "Internal error"}, 500


profiles_ns2.add_resource(ProfilesController, "/")
profiles_ns2.add_resource(ProfilesIdController, "/<string:profile_id>")
