"""Controller for /schedule."""

import logging
import datetime
import uuid

from flask_restx import Resource, fields, reqparse, inputs

from src.custom_exceptions import NotFoundException
from src.services import mission_schedule_services, mission_services
from src.utilities.custom_decorator import custom_jwt_required
from src.utilities.date_util import convert_str_to_date_time
from src.v1 import dto
from src.v1.dto.schedule_edit_type import ScheduleEditType
from src.version_handler import api_version_1_web

# Create module log
_logger = logging.getLogger(__name__)

schedule_ns2 = api_version_1_web.namespace(
    'schedule',
    description='Schedule Functionalities')

# Internal error response model
internal_server_error_model = schedule_ns2.model(
    "internal_server_error_model", {
        "message": fields.String(example="Internal server error")
    }
)

# Unauthorized response model
unauthorized_response_model = schedule_ns2.model(
    "unauthorized_response_model", {
        "message": fields.String(example="Not authorized")
    }
)

schedule_create_model = {
    "mission_id": fields.String(example=str(uuid.uuid4()),required=True),
    "schedule_cron": fields.String(example="5 4 * * *"),
    "schedule_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "start_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "timezone": fields.String(example="Asia/Kolkata"),
    "loop_count": fields.Integer(example=5)
}

schedule_row_dict = {
    "schedule_id": fields.String(
        example=str(uuid.uuid4()), required=True),
    "schedule_cron": fields.String(example="5 4 * * *"),
    "schedule_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "current_schedule_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "timezone": fields.String(example="Asia/Kolkata"),
    "start_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "loop_count": fields.Integer(example=5),
    "edit_type": fields.String(
        example=ScheduleEditType.THIS_EVENT.value,
        enum=[x.value for x in ScheduleEditType]
    )
}

schedule_search_dict = schedule_row_dict.copy()
schedule_search_dict.pop("timezone")
schedule_search_dict.pop("schedule_timestamp")
schedule_search_dict.update({
    'mission_id': fields.String(example=str(uuid.uuid4())),
    'timestamp': fields.String(example="'2021-03-10T14:00:00'")
})
schedule_search_dict.update({
    'cron': fields.String(example="11 9 * * 1"),
    'cron_job_start_date': fields.String(example="'2021-03-10T14:00:00'"),
    'schedule_type': fields.String(example="repeating")
})
schedule_pagination_dict = {
    "scheduled_missions": fields.List(fields.Nested(schedule_ns2.model(
        'schedule_row_dict',
        schedule_search_dict))),
    "last_updated_at" : fields.String(example="2021-03-01T14:00:00")
}

schedule_metadata_dict = schedule_search_dict.copy()
schedule_metadata_dict.update({
    'robot_id': fields.String(example=str(uuid.uuid4())),
    'timezone': fields.String(example="Asia/Kolkata"),
    'schedule_json': fields.String(example={
        "cron": "24 14 * * 1",
        "loop_count": 1
      })
})

# Schedule create model
schedule_create_model = schedule_ns2.model(
    'schedule_create_model', schedule_create_model)

# Schedule update model
schedule_update_model = schedule_ns2.model(
    'schedule_update_model', schedule_row_dict)

# Schedule delete model
schedule_delete_model = schedule_ns2.model(
    'schedule_delete_model', dto.schedule_delete_model)

schedule_get_parser = reqparse.RequestParser()
schedule_get_parser.add_argument(
    'robot_id', type=str, help='Robot ID for schedule', location='args',
    required=True)
schedule_get_parser.add_argument(
    'start_time', type=inputs.datetime_from_iso8601,
    help='start datetime in ISO 8601 format like 2021-05-03T13:56:20',
    location='args')
schedule_get_parser.add_argument(
    'end_time', type=inputs.datetime_from_iso8601,
    help='end datetime in ISO 8601 format like 2021-05-03T13:56:20',
    location='args')

columns = ("timestamp","mission_id","schedule_id","loop_count",
"mission_name","mission_instance_id")
schedule_get_parser.add_argument(
    'sort_by', type=str, choices=columns, help='Sort by which entry', location='args')
schedule_get_parser.add_argument(
    'sort_order', type=str, help='Sort by desc or asc', location='args')

# Schedule create response models
schedule_create_response_ok_model = schedule_ns2.model(
    "schedule_create_response_ok_model", {
        "schedule_id": fields.String(example=str(uuid.uuid4()))
    }
)
schedule_create_bad_response_model = schedule_ns2.model(
    "schedule_create_bad_response_model", {
        "message": fields.String(
            example="Bad request. Invalid input")
    }
)

# Schedule update response models
schedule_update_response_ok_model = schedule_ns2.model(
    "schedule_update_response_ok_model", schedule_row_dict
)
schedule_update_bad_response_model = schedule_ns2.model(
    "schedule_update_bad_response_model", {
        "message": fields.String(
            example="Bad request. Invalid input")
    }
)

# Schedule delete response models
schedule_delete_response_ok_model = schedule_ns2.model(
    "schedule_delete_response_ok_model", {
        "schedule_id": fields.String(example=str(uuid.uuid4()))
    }
)
schedule_delete_bad_response_model = schedule_ns2.model(
    "schedule_delete_bad_response_model", {
        "message": fields.String(example="Bad request. Invalid input")
    }
)

# Schedule search response models
schedule_search_response_ok_model = schedule_ns2.model(
    "schedule_search_response_ok_model", schedule_pagination_dict
)
schedule_search_bad_response_model = schedule_ns2.model(
    "schedule_search_bad_response_model", {
        "message": fields.String(
            example="Bad request. Invalid input")
    }
)

# Schedule meta data fetch response models
schedule_fetch_metadata_response_ok_model = schedule_ns2.model(
    'schedule_fetch_metadata_response_ok_model', schedule_metadata_dict
)
schedule_fetch_metadata_bad_response_model = schedule_ns2.model(
    'schedule_fetch_metadata_bad_response_model', {
        "message": fields.String(
            example="Bad request. Invalid input")
    }
)

# robot fetch latest timestamp response models
schedule_fetch_latest_timestamp_response_ok_model = schedule_ns2.model(
    'schedule_fetch_latest_timestamp_response_ok_model', {
        "message": fields.String(
        example="2021-03-08T12:00:00")
    }
)
schedule_fetch_latest_timestamp_bad_response_model = schedule_ns2.model(
    'schedule_fetch_latest_timestamp_bad_response_model', {
        "message": fields.String(
            example="Bad request. Invalid input")
    }
)


class ScheduleOperations(Resource):

    """Class for /schedule functionalities."""

    @schedule_ns2.expect(schedule_create_model)
    @custom_jwt_required()
    @schedule_ns2.response(200, "OK", schedule_create_response_ok_model)
    @schedule_ns2.response(400, "Bad Request", schedule_create_bad_response_model)
    @schedule_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @schedule_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def post(self):
        """Used to create a mission schedule"""
        # Check required fields
        try:
            request_data = schedule_ns2.payload
            mission_id = request_data['mission_id']
            timezone = request_data['timezone']
            schedule_cron = request_data.get('schedule_cron', None)
            schedule_timestamp = request_data.get('schedule_timestamp', None)
            start_timestamp = request_data.get('start_timestamp', None)
            loop_count = request_data.get('loop_count', 0)
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400
        try:
            # Ensure only one of cron or timestamp are provided
            if not schedule_timestamp and not schedule_cron:
                return {
                    "message": "One of cron or timestamp are required"}, 400
            if schedule_timestamp and schedule_cron:
                return {
                    "message": "Both cron and timestamp cannot be provided"
                        }, 400
            mission_details = mission_services.get_mission(mission_id)
            if not mission_details:
                return {"message": "mission not found"}, 400

            if start_timestamp:
                try:
                    convert_str_to_date_time(start_timestamp, "%Y-%m-%dT%H:%M:%S")
                except Exception as e:
                    _logger.debug(f"Request validation failed: {e}")
                    return {
                        "message": "start_timestamp in ISO 8601 format like 2021-05-03T13:56:20"
                    }, 400

            # Checking for existing schedules with same schedule cron or timestamp
            schedule_details = mission_schedule_services.get_schedule_list(
                mission_id=mission_id, schedule_cron=schedule_cron,
                schedule_timestamp=schedule_timestamp
            )
            if schedule_details:
                return {"message": "schedule already exists"}, 400

            robot_id = mission_details['robot_id']
            schedule_details = mission_schedule_services.create_schedule(
                robot_id, mission_id, timezone, schedule_cron,
                schedule_timestamp, loop_count, start_timestamp)
            return {"schedule_id": str(schedule_details.schedule_id)}, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400

    @schedule_ns2.expect(schedule_update_model)
    @custom_jwt_required()
    @schedule_ns2.response(200, "OK", schedule_update_response_ok_model)
    @schedule_ns2.response(
        400, "Bad Request", schedule_update_bad_response_model)
    @schedule_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @schedule_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def put(self):
        """Used to update a mission schedule"""
        # Check required fields
        try:
            request_data = schedule_ns2.payload
            schedule_id = request_data['schedule_id']
            schedule_cron = request_data.get('schedule_cron', None)
            schedule_timestamp = request_data.get('schedule_timestamp', None)
            current_schedule_timestamp = request_data.get('current_schedule_timestamp', None)
            start_timestamp = request_data.get('start_timestamp', None)
            timezone = request_data.get('timezone', None)
            loop_count = request_data.get('loop_count', None)
            edit_type = request_data.get('edit_type', None)
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400
        try:
            if schedule_timestamp and schedule_cron:
                return {
                    "message": "Both cron and timestamp cannot be provided"
                        }, 400
            if start_timestamp:
                try:
                    start_timestamp = convert_str_to_date_time(start_timestamp, "%Y-%m-%dT%H:%M:%S")
                except Exception as e:
                    _logger.debug(f"Request validation failed: {e}")
                    return {
                        "message": "start_timestamp in ISO 8601 format like 2021-05-03T13:56:20"
                    }, 400

            status, schedule_row = mission_schedule_services.update_schedule(
                schedule_id, timezone, schedule_cron,
                schedule_timestamp, loop_count, edit_type, current_schedule_timestamp,
                start_timestamp)
            if status:
                return schedule_row, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400  

    @schedule_ns2.expect(schedule_get_parser)
    @custom_jwt_required()
    @schedule_ns2.response(200, "OK", schedule_search_response_ok_model)
    @schedule_ns2.response(
        400, "Bad Request", schedule_search_bad_response_model)
    @schedule_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @schedule_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def get(self):
        """Used to retrieve all scheduled missions for robot."""
        try:
            args = schedule_get_parser.parse_args()
            #!Here starts the schedule mission sort
            sort_by = str(args.get("sort_by")) if args.get(
                "sort_by") else "timestamp"
            sort_order = str(args.get("sort_order")) if args.get(
                "sort_order") else "desc"
            if sort_order.lower() not in ["asc", "desc"]:
                return {"Message": "Invalid sort order"}, 400
            robot_id = args.get("robot_id")
            start_time = (args.get("start_time") if args.get("start_time")
                else datetime.datetime.utcnow())
            end_time = (args.get("end_time") if args.get("end_time")
                else (datetime.datetime.utcnow() +
                datetime.timedelta(hours=24)))
            scheduled_msns = dict(mission_schedule_services.get_scheduled_missions(
                robot_id, start_time, end_time))

            #!Sort by calling the function defined above
            sorted_ls = mission_schedule_services.scheduled_missions_sort(sort_by, 
                sort_order, scheduled_msns)
            scheduled_msns['scheduled_missions'] = sorted_ls
            if len(sorted_ls) == 0 or len(scheduled_msns) == 0:
                return {"scheduled_missions": []}, 200
            else:
                return scheduled_msns, 200
        except Exception as err:
            _logger.exception(err)
            return {"Message": str(err)}, 400


class ScheduleLastUpdated(Resource):

    """Class for schedule/latest_timestamp/<robot_id> functionalities"""

    @custom_jwt_required()
    @schedule_ns2.response(
        200, "OK", schedule_fetch_latest_timestamp_response_ok_model)
    @schedule_ns2.response(
        400, "Bad Request", schedule_fetch_latest_timestamp_bad_response_model)
    @schedule_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @schedule_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def get(self, robot_id):
        """Used to retrieve last updated time for schedule"""
        try:
            latest_updated_at = mission_schedule_services.get_latest_timestamp(
                robot_id)
            return latest_updated_at, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


class ScheduleByIdOperations(Resource):

    """Class for /schedule/<schedule_id> functionalities"""

    @schedule_ns2.expect(schedule_delete_model)
    @custom_jwt_required()
    @schedule_ns2.response(200, "OK", schedule_delete_response_ok_model)
    @schedule_ns2.response(
        400, "Bad Request", schedule_delete_bad_response_model)
    @schedule_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @schedule_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def delete(self, schedule_id):
        """Used to delete a mission schedule"""
        try:
            if mission_schedule_services.delete_schedule(
                schedule_id, schedule_ns2.payload or {}
            ):
                return {"schedule_id": str(schedule_id)}, 200
        except NotFoundException as err:
            _logger.exception(err)
            return {"message": str(err)}, 404
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


class ScheduleMetadata(Resource):

    """Class for /metadata/<schedule_id> functionalities."""

    @custom_jwt_required()
    @schedule_ns2.response(
        200, "OK", schedule_fetch_metadata_response_ok_model)
    @schedule_ns2.response(
        400, "Bad Request", schedule_fetch_metadata_bad_response_model)
    @schedule_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @schedule_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def get(self, schedule_id):
        """Used to retrieve metadata of a schedule"""
        try:
            schedule_metadata = mission_schedule_services.get_schedule(
                schedule_id)
            if not schedule_metadata:
                return {"message": "Schedule not found"}, 400
            msns_details = mission_services.get_mission(
                schedule_metadata['mission_id'])
            schedule_metadata['mission_name'] = msns_details['mission_name']
            return schedule_metadata, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


schedule_ns2.add_resource(ScheduleOperations, "/")
schedule_ns2.add_resource(ScheduleByIdOperations, "/<string:schedule_id>")
schedule_ns2.add_resource(
    ScheduleLastUpdated, "/latest_timestamp/<string:robot_id>")
schedule_ns2.add_resource(ScheduleMetadata, "/metadata/<string:schedule_id>")
