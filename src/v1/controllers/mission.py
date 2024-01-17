from flask_restx import Resource, fields
from src.version_handler import api_version_1_web
from src.services import mission_services
from src.utilities.custom_decorator import custom_jwt_required

missions_ns = api_version_1_web.namespace("missions", description="Missions Functionalities")

# Mission model for creation
mission_create_model = missions_ns.model(
    "MissionCreateModel",
    {
        "mission_name": fields.String(required=True, example="Mission Name"),
        "group_id": fields.String(example="group_id", required=True),
        "tasks": fields.List(fields.String(example="task_id"), required=True),
        "user_id": fields.String(example="user_id", required=True),
        "mission_schedule": fields.String(example="", required=True)
    },
)

# Mission model for update
mission_update_model = missions_ns.model(
    "MissionUpdateModel",
    {
        "mission_name": fields.String(required=False, example="New Mission Name"),
        "group_id": fields.String(example="new_group_id"),
        "tasks": fields.List(fields.String(example="task_id"))
        # Add other fields as necessary
    },
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
        try:
            missions = mission_services.get_all_missions()
            return {
                "message": "Missions fetched successfully",
                "missions": missions,
            }, 200
        except Exception as e:
            return {"message": str(e)}, 500

    @missions_ns.expect(mission_create_model)
    @missions_ns.response(201, "Mission Created", mission_response_model)
    @missions_ns.response(400, "Bad Request")
    @missions_ns.response(500, "Internal Server Error")
    def post(self):
        """Create a new mission."""
        try:
            data = missions_ns.payload
            mission = mission_services.create_mission(data)
            return {"message": "Mission created successfully", "mission": mission}, 201
        except Exception as e:
            return {"message": str(e)}, 500


class MissionIdController(Resource):
    """Controller for specific mission functionalities."""

    @missions_ns.expect(mission_update_model)
    @missions_ns.response(200, "Mission Updated", mission_response_model)
    @missions_ns.response(400, "Bad Request")
    @missions_ns.response(404, "Not Found")
    @missions_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def put(self, mission_id):
        """Update a specific mission."""
        try:
            data = missions_ns.payload
            mission = mission_services.update_mission(mission_id, data)
            if not mission:
                return {"message": "Mission not found"}, 404
            return {"message": "Mission updated successfully", "mission": mission}, 200
        except Exception as e:
            return {"message": str(e)}, 500

    @missions_ns.response(200, "Mission Deleted", mission_response_model)
    @missions_ns.response(404, "Not Found")
    @missions_ns.response(500, "Internal Server Error")
    @custom_jwt_required()
    def delete(self, mission_id):
        """Delete a specific mission."""
        try:
            result = mission_services.delete_mission(mission_id)
            if result:
                return {"message": "Mission deleted successfully"}, 200
            return {"message": "Mission not found"}, 404
        except Exception as e:
            return {"message": str(e)}, 500


# Add resources to namespace
missions_ns.add_resource(MissionsController, "/")
missions_ns.add_resource(MissionIdController, "/<string:mission_id>")
