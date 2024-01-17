# mission_schedule_controller.py
from flask_restx import Resource
from flask_jwt_extended import get_jwt_identity, get_jwt_claims
from src.services import mission_schedule_services
from src.utilities.custom_decorator import custom_jwt_required
from src.version_handler import api_version_1_web

mission_schedule_ns = api_version_1_web.namespace(
    "mission_schedule", description="Mission Schedule Operations"
)


class MissionScheduleController(Resource):
    @mission_schedule_ns.response(200, "Mission Schedule")
    @mission_schedule_ns.response(400, "Bad Request")
    @mission_schedule_ns.response(404, "Not Found")
    @mission_schedule_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def get(self, schedule_id):
        pass


class MissionScheduleUserController(Resource):
    @mission_schedule_ns.response(200, "Mission Schedule")
    @mission_schedule_ns.response(400, "Bad Request")
    @mission_schedule_ns.response(404, "Not Found")
    @mission_schedule_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def get(self):
        username = get_jwt_identity()
        schedule = mission_schedule_services.get_user_schedule(username)
        return {"schedule": schedule}, 200


# Add resources to namespace
mission_schedule_ns.add_resource(MissionScheduleController, "/<string:schedule_id>")
mission_schedule_ns.add_resource(MissionScheduleUserController, "/")
