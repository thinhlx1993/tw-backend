"""Controller for profiles."""
import json
import logging
from flask_restx import fields, Resource
from flask_jwt_extended import get_jwt_claims
from src.services import profiles_services, setting_services
from src.services import hma_services
from src.utilities.custom_decorator import custom_jwt_required
from src.version_handler import api_version_1_web
from src.parsers import profile_page_parser

# Create module log
_logger = logging.getLogger(__name__)

# Org fetch parser

profiles_ns2 = api_version_1_web.namespace(
    "profiles", description="Profiles Functionalities"
)

# username, password, fa, proxy, gpt_key, cookies, notes, status
profile_create_model = profiles_ns2.model(
    "profile_create_model",
    {
        "username": fields.String(example="username"),
        "password": fields.String(example="password"),
        "fa": fields.String(example="fa"),
        "proxy": fields.String(example="proxy"),
        "gpt_key": fields.String(example="gpt_key"),
        "cookies": fields.String(example="cookies"),
        "notes": fields.String(example="notes"),
        "status": fields.String(example="status"),
    },
)

profile_update_model = profiles_ns2.model(
    "profile_update_model",
    {
        "group_id": fields.String(example="group_id"),
        "username": fields.String(example="new_username"),
        "password": fields.String(example="new_password"),
        "fa": fields.String(example="new_fa"),
        "proxy": fields.String(example="new_proxy"),
        "gpt_key": fields.String(example="new_gpt_key"),
        "cookies": fields.String(example="new_cookies"),
        "notes": fields.String(example="new_notes"),
        "status": fields.String(example="new_status"),
        "data": fields.String(example="Profile metadata"),
    },
)

profile_operation_response_model = profiles_ns2.model(
    "profile_operation_response_model",
    {
        "message": fields.String(example="Operation successful"),
        "profile": fields.Nested(profile_update_model, description="Profile details"),
    },
)

# Internal error response model
internal_server_error_model = profiles_ns2.model(
    "internal_server_error_model",
    {"message": fields.String(example="Internal server error")},
)

# Unauthorized response model
unauthorized_response_model = profiles_ns2.model(
    "unauthorized_response_model", {"message": fields.String(example="Not authorized")}
)


class ProfilesController(Resource):
    """Class for / functionalities."""

    @profiles_ns2.expect(profile_page_parser)
    # @profiles_ns2.response(200, "OK", org_fetch_response_ok_model)
    # @profiles_ns2.response(400, "Bad Request", bad_response_model)
    @profiles_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def get(self):
        try:
            args = profile_page_parser.parse_args()
            # Pagination settings
            page = args.get("page", 1) if args.get("page") else None
            per_page = args.get("per_page") if args.get("per_page") else None
            # Sorts by 'teams_name' by default
            sort_by = str(args.get("sort_by")) if args.get("sort_by") else "created_at"
            # Sorts ascending by default
            sort_order = (
                str(args.get("sort_order")) if args.get("sort_order") else "asc"
            )
            if sort_order.lower() not in ["asc", "desc"]:
                return {"message": "Invalid sort order"}, 400
            # Read any filters specified
            search = args.get("search", "")
            group_id = args.get("group_id", "")
        except Exception as ex:
            return {"message": "Query data error"}, 500

        """Used to retrieve list of profiles"""
        profiles = profiles_services.get_all_profiles(
            page, per_page, sort_by, sort_order, search, group_id
        )

        return profiles, 200

    @profiles_ns2.expect(profile_create_model)
    # @org_ns2.response(200, "OK", org_create_response_ok_model)
    # @org_ns2.response(400, "Bad Request", org_create_bad_response_model)
    @profiles_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def post(self):
        """Used to create teams"""
        try:
            data = profiles_ns2.payload
            claims = get_jwt_claims()
            device_id = claims.get("device_id")
            user_id = claims.get("user_id")
        except Exception as e:
            _logger.debug(f"Data not valid: {e}")
            return {"message": "Data not valid"}, 400
        profile = profiles_services.create_profile(data, device_id, user_id)
        return {"profile_id": profile.profile_id}, 200


class ProfilesIdController(Resource):
    """Class for /profiles/profile_id functionalities."""

    @profiles_ns2.expect(
        profile_update_model
    )  # Assuming profile_update_model is defined for updating a profile
    @profiles_ns2.response(
        200, "Profile updated successfully", profile_operation_response_model
    )
    @profiles_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def put(self, profile_id):
        """Update a profile by ID"""
        try:
            data = profiles_ns2.payload
            profile = profiles_services.update_profile(profile_id, data)
            if not profile:
                return {"message": "Profile not found"}, 404
            return {
                "message": "Profile updated successfully",
                "profile": profile.repr_name(),
            }, 200
        except Exception as e:
            _logger.debug(f"Error updating profile: {e}")
            return {"message": "Data not valid or internal error"}, 400

    @profiles_ns2.response(
        200, "Profile deleted successfully", profile_operation_response_model
    )
    @profiles_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def delete(self, profile_id):
        """Delete a profile by ID"""
        try:
            claims = get_jwt_claims()
            device_id = claims.get("device_id")
            user_id = claims.get("user_id")
            result = profiles_services.delete_profile(profile_id, user_id, device_id)
            if result:
                return {"message": "Profile deleted successfully"}, 200
            return {"message": "Profile not found"}, 404
        except Exception as e:
            _logger.debug(f"Error deleting profile: {e}")
            return {"message": "Internal error"}, 500


class ProfilesBrowserController(Resource):
    @profiles_ns2.expect()
    @profiles_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def get(self, profile_id):
        """Used to retrieve profile's data"""
        profile = profiles_services.get_profile_by_id(profile_id)
        if not profile:
            return {"message": "profile not found"}, 400

        claims = get_jwt_claims()
        user_id = claims.get("user_id")
        device_id = claims.get("device_id")
        settings = setting_services.get_settings_by_user_device(user_id, device_id)
        settings = settings["settings"]
        browser_data = ""
        if settings["browserType"] == "HideMyAcc":
            hma_account = settings.get("hideMyAccAccount")
            hma_password = settings.get("hideMyAccPassword")
            hma_token = hma_services.get_hma_access_token(hma_account, hma_password)
            tz_data = hma_services.get_tz_data(profile)
            hma_result = hma_services.get_browser_data(
                hma_token, profile.hma_profile_id, tz_data
            )
            browser_data = hma_result["result"]
            profile.browser_data = browser_data

        return_data = profile.repr_name()
        return_data["browser_data"] = browser_data
        return_data["settings"] = settings
        return return_data, 200


profiles_ns2.add_resource(ProfilesController, "/")
profiles_ns2.add_resource(ProfilesIdController, "/<string:profile_id>")
profiles_ns2.add_resource(ProfilesBrowserController, "/<string:profile_id>/browserdata")
