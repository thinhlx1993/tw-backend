"""Services for missions"""

import logging
import datetime
import math
import uuid

from sentry_sdk import capture_exception
from sqlalchemy import text

from src import db
from src.models import Mission, MissionSchedule
from src.models.mission_instance import MissionInstance
from src.services import (
    mission_instance_services,
    mission_schedule_services
)


# Create module log
_logger = logging.getLogger(__name__)

def get_waypoint_mission_format(waypoint_id):
    """
    Get waypoint details in mission format
    :param str(uuid) waypoint_id: Unique ID for waypoint
    :return waypoint_details: Details of waypoint
    """
    try:
        waypoint_details = Waypoint.query.filter(
            Waypoint.waypoint_id==waypoint_id).first()
        if waypoint_details:
            return waypoint_details.mission_format()
        else:
            return None
    except Exception as err:
        capture_exception(err)
        raise


def create_mission(
    mission_name, robot_id, task_list, mission_id=str(uuid.uuid4())):
    """
    Create mission and mission-waypoint mappings
    :param str mission_name: Name of mission
    :param str(uuid) robot_id: Unique identifier for robot
    :param list task_list: List of tasks for mission
    :return new_mission: Newly created Mission
    """
    try:
        # Parse task list to get list of waypoints
        waypoint_list = get_waypoints_from_task_list(task_list)

        # Fill waypoint list with details
        mission_waypoint_list = [get_waypoint_mission_format(waypoint)
            for waypoint in waypoint_list]

        # Prepare mission_json
        mission_json = {
            "mission_name": mission_name,
            "tasks": task_list,
            "waypoints": mission_waypoint_list
        }

        # Add mission to table
        new_mission = Mission(mission_id, mission_name, robot_id, mission_json)
        db.session.add(new_mission)
        db.session.flush()

        # Create mission-waypoint mappings
        if waypoint_list:
            create_waypoint_mission_mappings(
                new_mission.mission_id,
                waypoint_list)
        return new_mission
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def update_mission(data):
    """
    Update a mission
    :param data: Dictionary with the following fields:
        uuid mission_id: Unique ID for each mission
        str mission_name: Mission name
        uuid robot_id: Unique ID for each robot
        list task_list: List of tasks for mission

    :return bool: True if successful
    """
    try:
        # Get row to update
        mission_row = Mission.query.filter(
            Mission.mission_id==data['mission_id']).first()

        # Recreate mission-waypoint mappings if task_list is redefined
        if data['task_list']:
            MissionWaypointMapping.query.filter_by(
                mission_id=mission_row.mission_id).delete()
            waypoint_list = get_waypoints_from_task_list(data['task_list'])
            if waypoint_list:
                create_waypoint_mission_mappings(
                    mission_row.mission_id,
                    waypoint_list)

            # Prepare mission_json
            mission_waypoint_list = [get_waypoint_mission_format(waypoint)
                for waypoint in waypoint_list]
            mission_name = (data['mission_name'] if data['mission_name']
                else mission_row.mission_name)
            mission_json = {
                "mission_name": mission_name,
                "tasks": data['task_list'],
                "waypoints": mission_waypoint_list
            }
        # Update mission_json if mission_name is updated
        elif data['mission_name']:
            mission_json = mission_row.mission_json.copy()
            mission_json['mission_name'] = data['mission_name']
        else:
            # Don't update mission_json if task_list or
            # mission_name isn't updated
            mission_json = None

        # Replace task_list with mission_json in update dictionary
        del data['task_list']
        data['mission_json'] = mission_json

        # If robot_id is provided in data, update robot_id for all schedules
        # under this mission and set last_updated_at to current time in utc
        if data["robot_id"]:
            schedule_list = (
                mission_schedule_services
                    .get_schedule_list_from_mission_id(data["mission_id"]))
            for schedule_row in schedule_list:
                schedule_row.robot_id = data["robot_id"]
                schedule_row.last_updated_at = datetime.datetime.utcnow()

        # Each value in 'data' is updated in the row, unless they're None
        for attribute in data:
            if data[attribute] is not None:
                setattr(mission_row, attribute, data[attribute])

        # Update the mission_json for related mission instances that have
        # start_timestamp > current time in utc.
        if data.get("mission_json"):
            mission_instance_services.update_mission_instances_from_mission(
                mission_json, data['mission_id'])

        db.session.flush()
        return True, mission_row.repr_name()
    except Exception as err:
        print(str(err))
        db.session.rollback()
        capture_exception(err)
        raise


def get_waypoints_from_task_list(task_list):
    """
    Get all waypoints from task_list
    :param list task_list: List of tasks to parse
    :return list waypoint_list: List of waypoints
    """
    waypoint_list = set()
    try:
        for task in task_list:
            if 'parameter' in task:
                parameter = task['parameter']
                if 'waypoint_id' in parameter:
                    waypoint_list.add(parameter['waypoint_id'])
        return list(waypoint_list)
    except:
        raise Exception("Failed to parse task list")


def create_waypoint_mission_mappings(mission_id, waypoint_list):
    """
    Create mappings between waypoints and mission
    :param str(uuid) mission_id: Unique identifier for mission
    :param list waypoint_list: List of waypoints
    :return bool: True if successful
    """
    try:
        for waypoint in waypoint_list:
            new_mission_waypoint_mapping = MissionWaypointMapping(
                mission_id, waypoint)
            db.session.add(new_mission_waypoint_mapping)
        db.session.flush()
        return True
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def delete_mission(mission_id):
    """
    Delete a mission
    :param mission_id: Unique ID for each mission
    :return bool: True if successful
    """
    try:
        # Get row to delete
        mission_row: Mission = Mission.query.filter(
            Mission.mission_id==mission_id).first()
        if not mission_row:
            raise Exception("Mission does not exist")
        
        # Soft deleting the mission
        mission_row.deleted_at = datetime.datetime.utcnow()

        MissionSchedule.query.filter(
            MissionSchedule.mission_id == mission_id,
        ).update({"deleted_at": datetime.datetime.utcnow()})

        MissionInstance.query.filter(
            MissionInstance.mission_id == mission_id,
            MissionInstance.start_timestamp >= datetime.datetime.utcnow()
        ).delete(synchronize_session=False)

        db.session.flush()
        return True
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def search_missions(page=0, per_page=10, sort_by="map_id",
    sort_order="desc", filters=None):
    """
    Search missions based on filters

    :param int page: page number of map
    :param int per_page: number of maps in a page
    :param str sort_by: Ordering parameter
    :param str sort_order: order by ascending or descending
    :param filters : filters for log
    :return status status of the response
    :return data data of the response
    """
    data = []
    out_data = {}
    try:
        column = getattr(Mission, sort_by, None)
        if not column:
            return False, {"Message": "Invalid sort_by Key provided"}
        sorting_order = sort_by + " " + sort_order
        query = Mission.query
        if isinstance(filters, dict) and filters.get('mission_name', None):
            search = f"%{filters.get('mission_name')}%"
            query = query.filter(Mission.mission_name.ilike(search))
            filters.pop('mission_name')
        status, query = dashboard_services.update_query(
            query, Mission, filters=filters)
        if not status:
            return False, query
        count = query.count()
        if sorting_order:
            query = query.order_by(text(sorting_order))
        if per_page and page:
            query = query.limit(per_page)
            query = query.offset(per_page*(page-1))

        # Formatting the result and adding schedules data
        data = []
        for i in query:
            mission_data = i.repr_name()
            schedules_list = (mission_schedule_services.
                        get_schedule_list_from_mission_id(i.mission_id))
            schedules = []
            for schedule in schedules_list:
                schedule_data = schedule.repr_name()
                if 'cron' in schedule.schedule_json:
                    schedule_info = {
			            "schedule_id": schedule_data['schedule_id'],
			            "cron": schedule_data['schedule_json']['cron'],
			            "type": "repeated"
		            }
                else:
                    schedule_info = {
                        "schedule_id": schedule_data['schedule_id'],
			            "timestamp": schedule_data['schedule_json']['timestamp'],
			            "type": "non-repeated"
                    }
                schedules.append(schedule_info)
            mission_data['schedules'] = schedules
            data.append(mission_data)

        out_data["data"] = data
        out_data["result_count"] = count
        if per_page:
            out_data["max_pages"] = math.ceil(count/per_page)
        db.session.flush()
    except Exception as err:
        _logger.exception(err)
        db.session.rollback()
        capture_exception(err)
        return False, {"Message": str(err)}
    return True, out_data


def get_mission(mission_id):
    """
    Get mission details
    :param str(uuid) mission_id: Unique ID for mission
    :return mission_details: Details of mission
    """
    try:
        mission_details = Mission.query.filter(
            Mission.mission_id==mission_id).first()
        if mission_details:
            return mission_details.repr_name()
        else:
            return None
    except Exception as err:
        capture_exception(err)
        raise

def filter_scheduled_missions(mission_ids):
    try:
        scheduled_missions = Mission.query\
        .join(MissionSchedule, MissionSchedule.mission_id == Mission.mission_id)\
        .filter(Mission.mission_id.in_(mission_ids))\
        .all()

        return scheduled_missions
    except Exception as err:
        capture_exception(err)
        raise