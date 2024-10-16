from flask_jwt_extended import get_jwt_claims
from flask_restx import Resource, fields

from src import cache, executor
from src.tasks.worker import delete_missions_schedule
from src.version_handler import api_version_1_web
from src.services import mission_services
from src.utilities.custom_decorator import custom_jwt_required

missions_ns = api_version_1_web.namespace(
    "missions", description="Missions Functionalities"
)

# Mission model for creation
mission_create_model = missions_ns.model(
    "MissionCreateModel",
    {
        "mission_name": fields.String(required=True, example="Mission Name"),
        "group_id": fields.String(
            example="80051754-c58a-4ab1-b29d-45c0e4c66dae", required=True
        ),
        "tasks": fields.List(
            fields.String(example="260a439d-0121-48c1-88e0-b09f4bfd780b"), required=True
        ),
        "profile_ids": fields.String(example="username1", required=True),
        "user_id": fields.String(
            example="a3213c22-c8c5-4e86-aa7c-ec4a08f0a7f9", required=True
        ),
        "mission_schedule": fields.List(
            fields.String(example="Monday", required=False, default=None)
        ),
        "start_date": fields.String(example="21:56", required=False),
        "config": fields.Raw(),
    },
)

mission_update_model = missions_ns.model(
    "MissionUpdateModel", {"force_start": fields.Boolean(required=True, example=True)}
)

# Mission response model
mission_response_model = missions_ns.model(
    "MissionResponseModel",
    {
        "message": fields.String(example="Operation successful"),
        "mission": fields.Nested(mission_create_model, description="Mission details"),
    },
)


class MissionsController(Resource):
    """Controller for missions functionalities."""

    @missions_ns.expect()
    @missions_ns.response(200, "OK", mission_response_model)
    @missions_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def get(self):
        """Retrieve a list of missions."""
        claims = get_jwt_claims()
        user_id = claims["user_id"]
        missions = mission_services.get_all_missions(user_id)
        return {
            "message": "Missions fetched successfully",
            "missions": missions,
        }, 200

    @missions_ns.expect(mission_create_model)
    @missions_ns.response(201, "Mission Created", mission_response_model)
    @missions_ns.response(400, "Bad Request")
    @missions_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def post(self):
        """Create a new mission."""
        data = missions_ns.payload
        mission = mission_services.create_mission(data)
        return {
            "message": "Mission created successfully",
            "mission": mission.repr_name(),
        }, 201


class MissionIdController(Resource):
    """Controller for specific mission functionalities."""

    @missions_ns.expect()
    @missions_ns.response(200, "Mission Started", mission_response_model)
    @missions_ns.response(400, "Bad Request")
    @missions_ns.response(404, "Not Found")
    @missions_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def post(self, mission_id):
        """Start a specific mission."""
        # data = missions_ns.payload
        # mission = mission_services.update_mission(mission_id, data)
        return {"message": "Mission started successfully", "mission": mission_id}, 200

    @missions_ns.expect(mission_update_model)
    @missions_ns.response(200, "Mission Updated", mission_response_model)
    @missions_ns.response(400, "Bad Request")
    @missions_ns.response(404, "Not Found")
    @missions_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def put(self, mission_id):
        """Start a specific mission."""
        data = missions_ns.payload
        mission = mission_services.update_mission(mission_id, data)
        return {"message": "Mission is updated", "mission": mission.repr_name()}, 200

    @missions_ns.response(200, "Mission Deleted", mission_response_model)
    @missions_ns.response(404, "Not Found")
    @missions_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def delete(self, mission_id):
        """Delete a specific mission."""
        mission = mission_services.get_missions_by_id(mission_id)
        if not mission:
            return {"message": "Mission not found"}, 404
        user_claims = get_jwt_claims()
        teams_id = user_claims["teams_id"]
        executor.submit(delete_missions_schedule, mission_id, teams_id)
        return {"message": "Delete the mission can take up to a minute"}, 200


# Add resources to namespace
missions_ns.add_resource(MissionsController, "/")
missions_ns.add_resource(MissionIdController, "/<string:mission_id>")
