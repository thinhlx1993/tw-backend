"""Controller for profiles."""
import random

from flask_restx import fields, Resource
from flask_jwt_extended import get_jwt_claims, get_jwt_identity
from src.services import profiles_services, setting_services
from src.services import hma_services, teams_services
from src.utilities.custom_decorator import custom_jwt_required
from src.version_handler import api_version_1_web
from src.parsers import profile_page_parser
from src.v1.enums.config import SettingsEnums

# Create module log
from src.log_config import _logger

# Org fetch parser

profiles_ns2 = api_version_1_web.namespace(
    "profiles", description="Profiles Functionalities"
)

profile_create_data = profiles_ns2.model(
    "create_model",
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
# username, password, fa, proxy, gpt_key, cookies, notes, status
profile_create_model = profiles_ns2.model(
    "profile_create_model",
    {"profiles": fields.List(fields.Nested(profile_create_data))},
)

profile_update_model = profiles_ns2.model(
    "profile_update_model",
    {
        "group_id": fields.String(example="group_id", require=False),
        "user_id": fields.String(example="user_id", require=False),
        "user_access": fields.String(example="user_access", require=False),
        "username": fields.String(example="new_username"),
        "password": fields.String(example="new_password"),
        "fa": fields.String(example="new_fa"),
        "proxy": fields.String(example="new_proxy"),
        "gpt_key": fields.String(example="new_gpt_key"),
        "cookies": fields.String(example="new_cookies"),
        "notes": fields.String(example="new_notes"),
        "status": fields.String(example="new_status"),
        "profile_data": fields.String(example="Profile metadata"),
    },
)

profile_hma_data_model = profiles_ns2.model(
    "profile_hma_data_model",
    {
        "tz": fields.Raw(
            required=False, example={"key": "value"}, description="JSON for tz"
        )
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
    @profiles_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def get(self):
        claims = get_jwt_claims()
        user_id = claims["user_id"]
        args = profile_page_parser.parse_args()
        # Pagination settings
        page = args.get("page", 1) if args.get("page") else None
        per_page = args.get("per_page") if args.get("per_page") else None
        # Sorts by 'teams_name' by default
        sort_by = str(args.get("sort_by")) if args.get("sort_by") else "created_at"
        # Sorts ascending by default
        sort_order = str(args.get("sort_order")) if args.get("sort_order") else "desc"
        if sort_order.lower() not in ["asc", "desc"]:
            return {"message": "Invalid sort order"}, 400
        # Read any filters specified
        search = args.get("search", "")
        group_id = args.get("group_id", "")
        """Used to retrieve list of profiles"""
        profiles = profiles_services.get_all_profiles(
            page, per_page, sort_by, sort_order, search, user_id
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
            request_data = profiles_ns2.payload
            claims = get_jwt_claims()
            device_id = claims.get("device_id")
            user_id = claims.get("user_id")
            teams_id = claims.get("teams_id")
        except Exception as e:
            _logger.debug(f"Data not valid: {e}")
            return {"message": "Data not valid"}, 400
        total_profiles = profiles_services.get_total_profiles()
        # teams = teams_services.get_teams(teams_id)
        # if total_profiles >= teams.teams_plan:
        #     return {
        #         "message": "Không thể tạo thêm profile do vượt quá số lượng cho phép, vui lòng liên hệ admin"
        #     }, 500

        success_number = 0
        error_number = 0
        for data in request_data.get("profiles"):
            try:
                data["owner"] = user_id  # set owner
                data["user_access"] = user_id
                profile = profiles_services.create_profile(data, device_id, user_id)
                if profile:
                    success_number += 1
            except Exception as ex:
                _logger.error(ex)
                if "HMA Account limit excelled" in str(ex):
                    return {"message": str(ex)}, 500
                if "Vui lòng cài đặt hệ thống" in str(ex):
                    return {"message": str(ex)}, 500
                error_number += 1
                # return {
                #     "message": f"Không thể tạo: {data['username']}, Đã tạo {success_number}"
                # }, 200
        # hma_services.clear_unused_resourced(device_id, user_id)
        return {
            "message": f"Tạo thành công {success_number}, Thất bại: {error_number}"
        }, 200


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
        data = profiles_ns2.payload
        profile = profiles_services.update_profile(profile_id, data)
        if not profile:
            return {"message": "Profile not found"}, 404
        return {
            "message": "Profile updated successfully",
            "profile": profile.repr_name(),
        }, 200

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
    @profiles_ns2.expect(profile_hma_data_model)
    @profiles_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def post(self, profile_id):
        """Used to retrieve profile's data"""
        body_data = profiles_ns2.payload

        _logger.info(f"tz info Client request data: {body_data}")
        profile = profiles_services.get_profile_by_id(profile_id)
        if not profile:
            return {"message": "profile not found"}, 400

        claims = get_jwt_claims()
        user_id = claims.get("user_id")
        device_id = claims.get("device_id")
        if profile.owner and profile.owner != user_id:
            return_data = {
                "username": profile.username
            }
            return return_data, 200

        settings = setting_services.get_settings_by_user_device(user_id, device_id)
        if not settings:
            return {"message": "Please setup your settings first"}, 400

        settings = settings["settings"]
        browser_data = ""
        if settings["browserType"] == SettingsEnums.hideMyAcc.value and body_data:
            # tz_data = hma_services.get_tz_data(profile)
            # _logger.info(f"tz info server request data: {tz_data}")
            hma_account = settings.get("hideMyAccAccount")
            hma_password = settings.get("hideMyAccPassword")
            hma_token = hma_services.get_hma_access_token(hma_account, hma_password)
            hma_result = hma_services.get_browser_data(
                hma_token, profile.hma_profile_id, body_data
            )
            browser_data = hma_result["result"]
            profile.browser_data = browser_data

        if not profile.debugger_port:
            debugger_port = random.randint(20000, 60000)
            profile.debugger_port = debugger_port

        return_data = profile.repr_name()
        return_data["browser_data"] = browser_data
        return_data["settings"] = settings
        return return_data, 200


class ProfilesByUserController(Resource):
    @profiles_ns2.expect()
    @profiles_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def get(self, user_id):
        # user_detail = user_services.get_user_details(user_id=user_id)
        profiles = profiles_services.get_user_profiles(user_id)
        return profiles, 200


class ProfilesOfUserController(Resource):
    @profiles_ns2.expect()
    @profiles_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @profiles_ns2.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def get(self):
        claims = get_jwt_claims()
        user_id = claims["user_id"]
        # user_detail = user_services.get_user_details(user_id=user_id)
        profiles = profiles_services.get_user_profiles(user_id)
        return profiles, 200


profiles_ns2.add_resource(ProfilesController, "/")
profiles_ns2.add_resource(ProfilesIdController, "/<string:profile_id>")
profiles_ns2.add_resource(ProfilesByUserController, "/user/<string:user_id>")
profiles_ns2.add_resource(ProfilesOfUserController, "/user")
profiles_ns2.add_resource(ProfilesBrowserController, "/<string:profile_id>/browserdata")
