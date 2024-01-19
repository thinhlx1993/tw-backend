from flask_restx import Resource, fields
from src.services import setting_services
from flask_jwt_extended import get_jwt_claims
from src.version_handler import api_version_1_web
from src.utilities.custom_decorator import custom_jwt_required

settings_ns = api_version_1_web.namespace(
    "settings", description="Settings Functionalities"
)

# Settings model for update or creation
settings_model = settings_ns.model(
    "SettingsModel",
    {
        "device_id": fields.String(
            required=True, example="ef79910e-6ef3-4b8d-af6d-ea7c367c2446"
        ),
        "settings": fields.Raw(
            description="Settings in JSON format",
        ),
    },
)

# Settings response model
settings_response_model = settings_ns.model(
    "SettingsResponseModel",
    {
        "message": fields.String(example="Operation successful"),
        "settings": fields.Nested(settings_model, description="Settings details"),
    },
)


class SettingsController(Resource):
    """Controller for settings functionalities."""

    @settings_ns.expect()
    @settings_ns.response(200, "OK", settings_response_model)
    @settings_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def get(self):
        """Retrieve a list of settings."""
        claims = get_jwt_claims()
        user_id = claims["user_id"]
        device_id = claims["device_id"]
        settings_records = setting_services.get_settings_by_user_device(
            user_id, device_id
        )
        return {
            "message": "Settings fetched successfully",
            "settings": settings_records,
        }, 200

    @settings_ns.expect(settings_model)
    @settings_ns.response(201, "Settings Updated/Created", settings_response_model)
    @settings_ns.response(400, "Bad Request")
    @settings_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def post(self):
        """Create or update settings."""
        data = settings_ns.payload
        claims = get_jwt_claims()
        user_id = claims["user_id"]
        device_id = claims["device_id"]
        settings_record = setting_services.create_or_update_settings(
            user_id, device_id, data["settings"]
        )
        return {
            "message": "Settings updated/created successfully",
            "settings": settings_record,
        }, 201

    @settings_ns.response(200, "Settings Deleted", settings_response_model)
    @settings_ns.response(404, "Not Found")
    @settings_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def delete(self):
        """Delete specific settings."""
        claims = get_jwt_claims()
        user_id = claims["user_id"]
        device_id = claims["device_id"]
        result = setting_services.delete_settings(user_id, device_id)
        if result:
            return {"message": "Settings deleted successfully"}, 200
        return {"message": "Settings not found"}, 404


# Add resources to namespace
settings_ns.add_resource(SettingsController, "/")
