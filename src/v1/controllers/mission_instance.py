"""Controller for /mission_instance."""

import logging
import os
import json
import uuid
import datetime

from flask_restx import Resource, fields, reqparse, inputs
from flask_jwt_extended import get_jwt_identity,get_jwt_claims

from src.version_handler import api_version_1_web
from src.parsers import page_parser
from src.utilities.custom_decorator import custom_jwt_required
from src.models import MissionInstance
from src.services import mission_instance_services, migration_services
from src.utilities import validator
from src.v1.controllers import utils

# Create module log
_logger = logging.getLogger(__name__)

ModelClass = MissionInstance
columns = [m.key for m in ModelClass.__table__.columns]

search_parser = page_parser.copy()
search_parser.replace_argument(
    'sort_by', type=str, choices=tuple(columns),
    help='Field to be sorted', location='args')
search_parser.add_argument(
    'teams_id', type=str, help='ID of the teams',
    location='args')
search_parser.add_argument(
    'distinct_field', type=str, choices=tuple(columns),
    help='Field to group by', location='args'
)

mission_instance_ns2 = api_version_1_web.namespace(
    'mission-instance',
    description='Mission Instance Functionalities')

parameter_model = {
    "waypoint_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab")
}

task_model = {
    "name": fields.String(example="toStart", required=True),
    "type": fields.String(example="MOV2POINT", required=True),
    "parameter": fields.Nested(mission_instance_ns2.model(
        'parameter_model', parameter_model))
}

task_list_update_model = {
    "mission_instance_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab", required=True),
    "task_status_list": fields.List(fields.String(example="completed")),
    "teams_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab", required=True),
    "timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "required_intervention": fields.Boolean(example=True),
    "is_complete": fields.Boolean(example=True),
    "success_category": fields.String(example="YELLOW"),
    "analysis_complete": fields.Boolean(example=True)
}

mission_json_model = {
    "mission_name": fields.String(example="Patrol Mission", required=True),
    "tasks": fields.List(fields.Nested(mission_instance_ns2.model(
        'task_model', task_model)))
}

issues_recorded_model = {
    "stopped": fields.Integer(example=1),
    "restarted": fields.Integer(example=1)
}

mission_instance_create_model = {
    "robot_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab", required=True),
    "mission_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "schedule_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "mission_json": fields.Nested(
        mission_instance_ns2.model('mission_json', mission_json_model)),
    "start_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "end_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "required_intervention": fields.Boolean(example=True),
    "is_cancelled": fields.Boolean(example=True),
    "is_deleted": fields.Boolean(example=True),
    "is_complete": fields.Boolean(example=True),
    "is_scheduled": fields.Boolean(example=True),
    "success_category": fields.String(example="YELLOW"),
    "issues_recorded": fields.Nested(
        mission_instance_ns2.model('issues_recorded', issues_recorded_model)
    ),
    "analysis_complete": fields.Boolean(example=True)
}

mission_instance_get_by_id_response_model = {
    "mission_instance_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "robot_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "robot_name": fields.String(example="Kabam Robot"),
    "mission_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "mission_name": fields.String(example="Patrol Mission"),
    "schedule_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "mission_json": fields.Nested(
        mission_instance_ns2.model('mission_json', mission_json_model)),
    "start_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "end_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "required_intervention": fields.Boolean(example=True),
    "is_cancelled": fields.Boolean(example=True),
    "is_deleted": fields.Boolean(example=True),
    "is_complete": fields.Boolean(example=True),
    "is_scheduled": fields.Boolean(example=True),
    "success_category": fields.String(example="YELLOW"),
    "issues_recorded": fields.Nested(
        mission_instance_ns2.model('issues_recorded', issues_recorded_model)
    ),
    "analysis_complete": fields.Boolean(example=True)
}

mission_instance_search_individual_response_model = {
    "mission_instance_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "robot_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "mission_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "schedule_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "mission_json": fields.Nested(
        mission_instance_ns2.model('mission_json', mission_json_model)),
    "start_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "end_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "required_intervention": fields.Boolean(example=True),
    "is_cancelled": fields.Boolean(example=True),
    "is_deleted": fields.Boolean(example=True),
    "is_complete": fields.Boolean(example=True),
    "is_scheduled": fields.Boolean(example=True),
    "success_category": fields.String(example="YELLOW"),
    "issues_recorded": fields.Nested(
        mission_instance_ns2.model('issues_recorded', issues_recorded_model)
    ),
    "analysis_complete": fields.Boolean(example=True)
}

mission_instance_delete_model = {
    "mission_instance_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab", required=True)
}

mission_instance_update_model = {
    "mission_instance_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab", required=True),
    "robot_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "mission_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "schedule_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "mission_json": fields.Nested(mission_instance_ns2.model(
        'mission_json', mission_json_model)),
    "start_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "end_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "required_intervention": fields.Boolean(example=True),
    "is_cancelled": fields.Boolean(example=True),
    "is_deleted": fields.Boolean(example=True),
    "is_complete": fields.Boolean(example=True),
    "is_scheduled": fields.Boolean(example=True),
    "success_category": fields.String(example="YELLOW"),
    "issues_recorded": fields.Nested(
        mission_instance_ns2.model('issues_recorded', issues_recorded_model)
    ),
    "analysis_complete": fields.Boolean(example=True)
}

mission_instance_update_response_model = {
    "mission_instance_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab", required=True),
    "robot_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "robot_name": fields.String(example="Kabam Robot"),
    "mission_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "mission_name": fields.String(example="Patrol Mission"),
    "schedule_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab"),
    "mission_json": fields.Nested(mission_instance_ns2.model(
        'mission_json', mission_json_model)),
    "start_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "end_timestamp": fields.DateTime(example='2021-03-10T14:00:00'),
    "required_intervention": fields.Boolean(example=True),
    "is_cancelled": fields.Boolean(example=True),
    "is_deleted": fields.Boolean(example=True),
    "is_complete": fields.Boolean(example=True),
    "is_scheduled": fields.Boolean(example=True),
    "success_category": fields.String(example="YELLOW"),
    "issues_recorded": fields.Nested(
        mission_instance_ns2.model('issues_recorded', issues_recorded_model)
    ),
    "analysis_complete": fields.Boolean(example=True)
}

mission_instance_search_response_model = {
    "data": fields.List(fields.Nested(mission_instance_ns2.model(
        'mission_instance_search_individual_response_model',
        mission_instance_search_individual_response_model))),
    "result_count" : fields.Integer(example=1),
    "max_pages": fields.Integer(example=1)
}

mission_instance_delete_response_model = {
    "message" : fields.String(
        example = "Mission Instance has been deleted")
}

unauthorized_response_model = {
    "msg": fields.String(example="Missing Authorization Header")
}

exception_response_model = {
    "message": fields.String(example="Failed because (Exception)")
}

mission_instance_create_response_model = {
    "mission_instance_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab")
}

mission_instance_export_success_response_model = {
    "task_id": fields.String(
        example="17b0ac53-76fa-47fd-a6bf-d2acef4f87ab")
}

mission_export_parser = reqparse.RequestParser()
mission_export_parser.add_argument('robot_id_list', type=str, action='append',
 help='Filter by robot id', required=False)
mission_export_parser.add_argument('property_id_list', type=str, action='append',
 help='Filter by property id', required=False)
mission_export_parser.add_argument('timezone', type=str,
 help='Required timezone', required=False)
mission_export_parser.add_argument('is_scheduled', type=bool,
help='Get only scheduled mission data', required=False)
mission_export_parser.add_argument('start_date', type=inputs.datetime_from_iso8601,
 required=True, help='start datetime in ISO 8601 format like 2021-02-09T16:56:20', location='args')
mission_export_parser.add_argument('end_date', type=inputs.datetime_from_iso8601,
  required=True, help='end datetime in ISO 8601 format like 2021-05-03T13:56:20', location='args')

mission_instance_get_by_id_response_model = mission_instance_ns2.model(
    'mission_instance_get_by_id_response_model',
    mission_instance_get_by_id_response_model
)

mission_instance_create_response_model = mission_instance_ns2.model(
    'mission_instance_create_response_model',
    mission_instance_create_response_model
)

mission_instance_delete_response_model = mission_instance_ns2.model(
    'mission_instance_delete_response_model',
    mission_instance_delete_response_model
)

mission_instance_create_model = mission_instance_ns2.model(
    'mission_instance_create_model', mission_instance_create_model
)

mission_instance_delete_model = mission_instance_ns2.model(
    "mission_instance_delete_model", mission_instance_delete_model
)

mission_instance_update_model = mission_instance_ns2.model(
    "mission_instance_update_model", mission_instance_update_model
)

mission_instance_update_response_model = mission_instance_ns2.model(
    "mission_instance_update_response_model", mission_instance_update_response_model
)

task_list_update_model = mission_instance_ns2.model(
    'task_list_update_model', task_list_update_model
)

unauthorized_response_model = mission_instance_ns2.model(
    'unauthorized_response_model', unauthorized_response_model
)

exception_response_model = mission_instance_ns2.model(
    'exception_response_model', exception_response_model
)

mission_instance_search_response_model = mission_instance_ns2.model(
    'mission_instance_search_response_model',
    mission_instance_search_response_model
)

mission_instance_export_success_response_model = mission_instance_ns2.model(
    'mission_instance_export_success_response_model',mission_instance_export_success_response_model
)

class MissionInstanceOperations(Resource):
    """Functionalities for MissionInstance"""
    @mission_instance_ns2.expect(mission_instance_create_model)
    @mission_instance_ns2.response(
        200, "Success", mission_instance_create_response_model)
    @mission_instance_ns2.response(
        400, "Failed", exception_response_model)
    @mission_instance_ns2.response(
        401, "Unauthorized", unauthorized_response_model)
    @custom_jwt_required()
    def post(self):
        """Used to create mission_instance"""
        try:
            data = mission_instance_ns2.payload
            robot_id = data['robot_id']
            mission_id = data.get('mission_id', None)
            start_timestamp = data['start_timestamp']
            mission_json = data.get('mission_json', None)
            issues_recorded = data.get('issues_recorded', None)
            end_timestamp = data.get('end_timestamp', None)
            is_deleted = data.get('is_deleted', None)
            is_complete = data.get('is_complete', None)
            required_intervention = data.get('required_intervention', None)
            success_category = data.get('success_category', None)
            is_cancelled = data.get('is_cancelled', None)
            is_scheduled = data.get('is_scheduled', None)
            analysis_complete = data.get('analysis_complete', None)
            if 'schedule_id' in data and len(data['schedule_id'])>0: 
                schedule_id = data['schedule_id']
            else:
                schedule_id = None
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400
        try:
            # mission_instance = (
            #     mission_instance_services.
            #     get_mission_instance_from_timestamp_and_schedule_id(
            #         mission_id=mission_id,
            #         timestamp=start_timestamp, schedule_id=False))
            # If mission instance at start_timestamp does not exists
            # create mission_instance
            # if not mission_instance:
            new_mission_instance = (
                mission_instance_services.create_mission_instance(
                    robot_id, start_timestamp, mission_json, mission_id,
                    issues_recorded, end_timestamp, schedule_id,
                    is_deleted, is_complete, required_intervention,
                    success_category, is_cancelled, analysis_complete))
            return {
                "mission_instance_id": str(
                    new_mission_instance.mission_instance_id)
            }, 200

            # If mission instance at start_timestamp exists, check if input is
            # adhoc mission, delete existing mission instance and create new
            # mission instance
            # elif not schedule_id:
            #     delete_mission_instance_dict = {
            #         'mission_instance_id': mission_instance.mission_instance_id,
            #         'is_deleted': True
            #     }
            #     mission_instance = (
            #         mission_instance_services.update_mission_instance(
            #         delete_mission_instance_dict))
            #     new_mission_instance = (
            #         mission_instance_services.create_mission_instance(
            #             mission_id, start_timestamp, mission_json,
            #             issues_recorded, end_timestamp, schedule_id,
            #             is_deleted, is_complete, required_intervention,
            #             success_category, is_cancelled, analysis_complete))
            #     return ({
            #                 "mission_instance_id":
            #                     str(new_mission_instance.mission_instance_id)
            #             }, 200)
            # else:
            #     return {"message": "mission_instance already exists"}, 400

        except Exception as err:
            _logger.exception(err)
            return {"message": "Failed because " + str(err)}, 400

    @mission_instance_ns2.expect(search_parser)
    @mission_instance_ns2.response(
        200, "Success", mission_instance_search_response_model)
    @mission_instance_ns2.response(
        400, "Failed", exception_response_model)
    @mission_instance_ns2.response(
        401, "Unauthorized", unauthorized_response_model)
    @custom_jwt_required()
    def get(self):
        """Used to retrieve list of mission_instances"""
        try:
            args = search_parser.parse_args()
            teams_id = args.get("teams_id", None)
            try:
                user_identity = get_jwt_identity()
                if teams_id != None and user_identity == "admin":
                    migration_services.set_search_path(teams_id)
            except Exception as err:
                _logger.exception(err)
                return {
                    "message": "Could not set teams for request"
                    }, 400
            page = args.get("page", 1) if args.get("page") else 1
            per_page = args.get("per_page", 50) if args.get("per_page") else 50
            sort_by = str(args.get("sort_by")) if args.get(
                "sort_by") else "start_timestamp"
            sort_order = str(args.get("sort_order")) if args.get(
                "sort_order") else "asc"
            distinct_field = args.get("distinct_field", None)
            filters = json.loads(args.get("filter")
                                 ) if args.get("filter") else None
            if sort_order.lower() not in ["asc", "desc"]:
                return {"message": "Invalid sort order"}, 400
            status, result = mission_instance_services.search_mission_instance(
                sort_by=sort_by, sort_order=sort_order,
                page=page, per_page=per_page,
                distinct_field=distinct_field, filters=filters)
            if status:
                return result, 200
            else:
                return result, 400
        except Exception as err:
            _logger.exception(err)
            return {"message": "Failed because " + str(err)}, 400

    @mission_instance_ns2.expect(mission_instance_update_model)
    @mission_instance_ns2.response(
        200, "Success", mission_instance_update_response_model)
    @mission_instance_ns2.response(
        400, "Failed", exception_response_model)
    @mission_instance_ns2.response(
        401, "Unauthorized", unauthorized_response_model)
    @custom_jwt_required()
    def put(self):
        """Used to update a mission_instance"""
        try:
            data = mission_instance_ns2.payload
            mission_instance_id = data["mission_instance_id"]
            teams_id = data.get("teams_id", None)
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400
        try:
            user_identity = get_jwt_identity()
            if teams_id != None and user_identity == "admin":
                migration_services.set_search_path(teams_id)
        except Exception as err:
            _logger.exception(err)
            return {
                "message": "Could not set teams for request"
                }, 400
        try:
            robot_id = data.get('robot_id', None)
            schedule_id = data.get('schedule_id', None)
            start_timestamp = data.get('start_timestamp', None)
            mission_id = data.get('mission_id', None)
            mission_json = data.get('mission_json', None)
            issues_recorded = data.get('issues_recorded', None)
            end_timestamp = data.get('end_timestamp', None)
            is_deleted = data.get('is_deleted', None)
            is_complete = data.get('is_complete', None)
            required_intervention = data.get('required_intervention', None)
            success_category = data.get('success_category', None)
            is_cancelled = data.get('is_cancelled', None)
            is_scheduled = data.get('is_scheduled', None)
            analysis_complete = data.get('analysis_complete', None)
            update_dict = {
                'mission_instance_id': mission_instance_id,
                'robot_id': robot_id,
                'mission_id': mission_id,
                'schedule_id': schedule_id,
                'start_timestamp': start_timestamp,
                'mission_json': mission_json,
                'issues_recorded': issues_recorded,
                'end_timestamp': end_timestamp,
                'is_deleted': is_deleted,
                'is_complete': is_complete,
                'required_intervention': required_intervention,
                'success_category': success_category,
                'is_cancelled': is_cancelled,
                'is_scheduled': is_scheduled,
                'analysis_complete': analysis_complete
            }
            mission_instance = (
                mission_instance_services.update_mission_instance(
                update_dict))
            if mission_instance:
                return mission_instance.repr_name(), 200
            else:
                return{"message": "Could not update mission_instance"}, 400
        except Exception as err:
            _logger.exception(err)
            return {"message": "Failed because " + str(err)}, 400


class UpdateTaskList(Resource):
    @mission_instance_ns2.response(
        200, "Success", mission_instance_update_response_model)
    @mission_instance_ns2.response(
        400, "Failed", exception_response_model)
    @mission_instance_ns2.response(
        401, "Unauthorized", unauthorized_response_model)
    @mission_instance_ns2.expect(task_list_update_model)
    @custom_jwt_required()
    def put(self):
        """Used to update tasklist of mission_instances"""
        try:
            data = mission_instance_ns2.payload
            mission_instance_id = data['mission_instance_id']
            teams_id = data.get('teams_id', None)
            timestamp = data['timestamp']
            task_status_list = data.get('task_status_list', None)
            success_category = data.get('success_category', None)
            required_intervention = data.get('required_intervention', None)
            is_complete = data.get('is_complete', None)
            analysis_complete = data.get('analysis_complete', None)
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400
        try:
            user_identity = get_jwt_identity()
            if user_identity == "admin":
                migration_services.set_search_path(teams_id)
        except Exception as err:
            _logger.exception(err)
            return {
                "message": "Could not set teams for request"
            }, 400
        try:
            if is_complete:
                end_timestamp = timestamp
            else:
                end_timestamp = None
            update_dict = {
                "mission_instance_id": mission_instance_id,
                "task_status_list": task_status_list,
                "end_timestamp": end_timestamp,
                "success_category": success_category,
                "required_intervention": required_intervention,
                "is_complete": is_complete,
                "timestamp": timestamp,
                "analysis_complete": analysis_complete
            }
            data = mission_instance_services.update_task_status(
                update_dict)
            return data, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": "Failed because " + str(err)}, 400


class MissionInstanceByID(Resource):
    @custom_jwt_required()
    @mission_instance_ns2.response(
        200, "Success", mission_instance_get_by_id_response_model)
    @mission_instance_ns2.response(
        400, "Failed", exception_response_model)
    @mission_instance_ns2.response(
        401, "Unauthorized", unauthorized_response_model)
    def get(self, mission_instance_id):
        """Used to retrieve a mission_instance"""
        try:
            mission_instance_details = (
                mission_instance_services.get_mission_instance(
                    mission_instance_id))
            return mission_instance_details, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": "Failed because " + str(err)}, 400

    @custom_jwt_required()
    @mission_instance_ns2.response(
        200, "Success", mission_instance_delete_response_model)
    @mission_instance_ns2.response(
        400, "Failed", exception_response_model)
    @mission_instance_ns2.response(
        401, "Unauthorized", unauthorized_response_model)
    def delete(self, mission_instance_id):
        """Used to delete a mission_instance"""
        try:
            status = mission_instance_services.delete_mission_instance(
                mission_instance_id)
            if status:
                return ({
                    "message": "Mission Instance has been deleted"}, 200)
            else:
                return {"message": "Could not delete mission_instance"}, 400
        except Exception as err:
            _logger.exception(err)
            return {"message": "Failed because " + str(err)}, 400

class MissionMetricsExport(Resource):
    @custom_jwt_required()
    @mission_instance_ns2.expect(mission_export_parser)
    @mission_instance_ns2.response(
        200, "Success", mission_instance_export_success_response_model
    )
    @mission_instance_ns2.response(400, "Failed", exception_response_model)
    @mission_instance_ns2.response(401, "Unauthorized", unauthorized_response_model)
    def get(self):
        """Used to trigger mission metrics export"""
        try:
            user_claims = get_jwt_claims()
            args = mission_export_parser.parse_args()
            start_date = args.get("start_date", None)
            end_date = args.get("end_date", None)
            robot_id_list = args.get("robot_id_list", None)
            property_id_list = args.get("property_id_list", None)
            timezone = args.get("timezone", None)
            is_scheduled = args.get("is_scheduled", None)

            if not timezone:
                timezone = "UTC"
            if robot_id_list:
                validator.validate_uuid_list(robot_id_list)
            if property_id_list:
                validator.validate_uuid_list(property_id_list)
            validator.validate_timezone(timezone)
            if start_date >= end_date:
                raise ValueError("Start datetime should be less than end datetime")
            # Generate a task UUID for celery
            task_uuid = str(uuid.uuid4())
            # Set celery task status to pending in celery table
            celery_services.add_celery_task(
                task_id=task_uuid, status="PENDING", s3_url=""
            )
            # Call the Celery task to export the CSV data to S3
            task = export_mission_metrics.apply_async(
                args=[
                    start_date,
                    end_date,
                    robot_id_list,
                    property_id_list,
                    timezone,
                    is_scheduled,
                    user_claims["teams_id"],
                    "mission-export",
                    utils.get_s3_folder_name(os.environ["DASHBOARD_DOMAIN"])
                    + "mission_metrics_"
                    + user_claims["user_id"]
                    + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    + ".csv",
                ],
                task_id=task_uuid,
            )
            return {"task_id": task.id}
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400

mission_instance_ns2.add_resource(MissionInstanceOperations, "/")
mission_instance_ns2.add_resource(
    MissionInstanceByID, "/<mission_instance_id>")
mission_instance_ns2.add_resource(
    UpdateTaskList, "/task-list")
mission_instance_ns2.add_resource(
    MissionMetricsExport, "/export")
