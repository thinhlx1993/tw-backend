"""Controller for /mission."""

import logging
import json
import uuid

from flask_restx import Resource, fields

from src.version_handler import api_version_1_web
from src.parsers import page_parser
from src.services import mission_services
from src.models import Mission
from src.utilities.custom_decorator import custom_jwt_required

# Create module log
_logger = logging.getLogger(__name__)

mission_ns2 = api_version_1_web.namespace(
    'mission',
    description='Mission Functionalities')

# Internal error response model
internal_server_error_model = mission_ns2.model(
    "internal_server_error_model", {
        "message": fields.String(example="Internal server error")
    }
)

# Unauthorized response model
unauthorized_response_model = mission_ns2.model(
    "unauthorized_response_model", {
        "message": fields.String(example="Not authorized")
    }
)

Model = Mission
columns = [m.key for m in Model.__table__.columns]

search_parser = page_parser.copy()
search_parser.replace_argument(
    'sort_by', type=str, choices=tuple(columns),
    help='Field to be sorted', location='args')

parameter_model = {
    "waypoint_id": fields.String(example=str(uuid.uuid4()))
}

schedule_model = {
    "schedule_id": fields.String(example=str(uuid.uuid4()), required=True),
    "timestamp": fields.String(example="2023-02-10T14:05+05:30", required=True),
    "type": fields.String(example="non-repeated", required=True)
}

task_model = {
    "name": fields.String(example="toStart", required=True),
    "type": fields.String(example="MOV2POINT", required=True),
    "parameter": fields.Nested(mission_ns2.model(
        'parameter_model', parameter_model))
}

mission_create_model = {
    "mission_name": fields.String(example="Patrol Mission", required=True),
    "robot_id": fields.String(
        example=str(uuid.uuid4()), required=True),
    "task_list": fields.List(fields.Nested(mission_ns2.model(
        'task_model', task_model)))
}

mission_row_dict = mission_create_model.copy()
mission_row_dict['mission_id'] = fields.String(
    example=str(uuid.uuid4()), required=True)

mission_fetch_dict = mission_row_dict.copy()
mission_fetch_dict["schedules"] = fields.List(fields.Nested(mission_ns2.model(
        'schedule_model', schedule_model)))

mission_pagination_dict = {
    "data": fields.List(
        fields.Nested(
            mission_ns2.model('mission_fetch_dict', mission_fetch_dict))),
    "result_count" : fields.Integer(example=1),
    "max_pages": fields.Integer(example=1)
}

# Mission create model
mission_create_model = mission_ns2.model(
    'mission_create_model', mission_create_model)

# Mission update model
mission_update_model = mission_ns2.model(
    'mission_update_model', mission_row_dict)

# Mission create response models
mission_create_response_ok_model = mission_ns2.model(
    "mission_create_response_ok_model", {
        "mission_id": fields.String(example=str(uuid.uuid4()))
    }
)
mission_create_bad_response_model = mission_ns2.model(
    "mission_create_bad_response_model", {
        "message": fields.String(example="Bad request. Invalid input")
    }
)

# Mission fetch response models
mission_fetch_response_ok_model = mission_ns2.model(
    "mission_fetch_response_ok_model", mission_row_dict
)
mission_fetch_bad_response_model = mission_ns2.model(
    "mission_fetch_bad_response_model", {
        "message": fields.String(example="Bad request. Invalid input")
    }
)

# Mission update response models
mission_update_response_ok_model = mission_ns2.model(
    "mission_update_response_ok_model", mission_row_dict
)
mission_update_bad_response_model = mission_ns2.model(
    "mission_update_bad_response_model", {
        "message": fields.String(example="Bad request. Invalid input")
    }
)

# Mission search response models
mission_search_response_ok_model = mission_ns2.model(
    "mission_search_response_ok_model", mission_pagination_dict
)
mission_search_bad_response_model = mission_ns2.model(
    "mission_search_bad_response_model", {
        "message": fields.String(example="Bad request. Invalid input")
    }
)

# Mission delete response models
mission_delete_response_ok_model = mission_ns2.model(
    "mission_delete_response_ok_model", {
        "mission_id": fields.String(example=str(uuid.uuid4()))
    }
)
mission_delete_bad_response_model = mission_ns2.model(
    "mission_delete_bad_response_model", {
        "message": fields.String(example="Bad request. Invalid input")
    }
)

class MissionOperations(Resource):

    """Class for /mission functionalities"""

    @custom_jwt_required()
    @mission_ns2.expect(mission_create_model)
    @mission_ns2.response(200, "OK", mission_create_response_ok_model)
    @mission_ns2.response(
        400, "Bad Request", mission_create_bad_response_model)
    @mission_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @mission_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def post(self):
        """Used to create a mission"""
        try:
            request_data = mission_ns2.payload
            mission_name = request_data['mission_name']
            robot_id = request_data['robot_id']
            task_list = request_data['task_list']
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400
        try:
            mission_details = mission_services.create_mission(
                mission_name, robot_id, task_list)
            return {"mission_id": str(mission_details.mission_id)}, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400

    @mission_ns2.expect(mission_update_model)
    @custom_jwt_required()
    @mission_ns2.response(200, "OK", mission_update_response_ok_model)
    @mission_ns2.response(
        400, "Bad Request", mission_update_bad_response_model)
    @mission_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @mission_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def put(self):
        """Used to update a mission"""
        try:
            request_data = mission_ns2.payload
            mission_id = request_data['mission_id']
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request.Provide mission_id"}, 400
        try:
            mission_name = (request_data['mission_name'] if 'mission_name'
                in request_data else None)
            robot_id = (request_data['robot_id'] if 'robot_id'
                in request_data else None)
            task_list = (request_data['task_list'] if 'task_list'
                in request_data else None)

            update_dict = {
                "mission_id": mission_id,
                "mission_name": mission_name,
                "robot_id": robot_id,
                "task_list": task_list
            }
            status, mission_row = mission_services.update_mission(update_dict)
            if status:
                return mission_row, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400

    @mission_ns2.expect(search_parser)
    @custom_jwt_required()
    @mission_ns2.response(200, "OK", mission_search_response_ok_model)
    @mission_ns2.response(
        400, "Bad Request", mission_search_bad_response_model)
    @mission_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @mission_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def get(self):
        """Used to retrieve list of missions"""
        try:
            args = search_parser.parse_args()
            page = args.get("page", 1) if args.get("page") else 1
            per_page = args.get("per_page", 50) if args.get("per_page") else 50
            sort_by = str(args.get("sort_by")) if args.get(
                "sort_by") else "robot_id"
            sort_order = str(args.get("sort_order")) if args.get(
                "sort_order") else "desc"

            filters = json.loads(args.get("filter")
                                 ) if args.get("filter") else None
            if sort_order.lower() not in ["asc", "desc"]:
                return {"message": "Invalid sort order"}, 400
            status, result = mission_services.search_missions(
                sort_by=sort_by, sort_order=sort_order, page=page,
                per_page=per_page, filters=filters)
            if status:
                return result, 200
            else:
                return result, 400
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


class MissionByIdOperations(Resource):

    """Class for /mission/<mission_id> functionalities"""

    @custom_jwt_required()
    @mission_ns2.response(200, "OK", mission_fetch_response_ok_model)
    @mission_ns2.response(400, "Bad Request", mission_fetch_bad_response_model)
    @mission_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @mission_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def get(self, mission_id):
        """Used to retrieve a mission"""
        try:
            mission_details = mission_services.get_mission(mission_id)
            return mission_details, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


    @custom_jwt_required()
    @mission_ns2.response(200, "OK", mission_delete_response_ok_model)
    @mission_ns2.response(
        400, "Bad Request", mission_delete_bad_response_model)
    @mission_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @mission_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def delete(self, mission_id):
        """Used to delete a mission"""
        try:
            if mission_services.delete_mission(mission_id):
                return {"mission_id": str(mission_id)}, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


mission_ns2.add_resource(MissionOperations, "/")
mission_ns2.add_resource(MissionByIdOperations, "/<string:mission_id>")
