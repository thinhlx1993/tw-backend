"""Services for mission_instance"""

import logging
import datetime
import math
import time

from dateutil import tz
from sentry_sdk import capture_exception
from sqlalchemy import and_, text
from sqlalchemy.exc import TimeoutError
from sqlalchemy.orm.attributes import flag_modified

from src import db, app
from src.models import MissionInstance, Mission, Robot, MissionSchedule
from src.utilities.date_util import convert_iso_str_to_date_time

# Create module log
_logger = logging.getLogger(__name__)

MISSION_TASK_UPDATE_MAX_RETRY = 3


def get_mission_instance_from_timestamp_and_schedule_id(
    mission_id, schedule_id, timestamp, is_deleted=[False]
):
    """Get mission_instance details from timestamp and schedule_id.

    :param str(uuid) schedule_id: Unique ID for schedule
    :param str(datetime) timestamp: start_timestamp for mission_instance
    :param list(boolean) is_deleted: filter rows according to 'is_deleted'
    :return mission_instance_details: Details of mission_instance
    """
    try:
        if schedule_id is False:
            # Fetches record with start_timestamp schedule_id is not considered
            mission_instance = (
                MissionInstance.query.filter(
                    MissionInstance.start_timestamp == timestamp,
                    MissionInstance.is_deleted == False,
                )
                .join(Mission, MissionInstance.mission_id == Mission.mission_id)
                .join(Robot, Robot.robot_id == Mission.robot_id)
                .filter(Mission.mission_id == mission_id)
                .first()
            )
        else:
            # Fetch record with start_timestamp and schedule_id
            mission_instance = (
                MissionInstance.query.filter(
                    MissionInstance.schedule_id == schedule_id,
                    MissionInstance.start_timestamp == timestamp,
                    MissionInstance.is_deleted.in_(is_deleted),
                )
                .join(
                    Mission, MissionInstance.mission_instance_id == Mission.mission_id
                )
                .join(Robot, Mission.robot_id == Robot.robot_id)
                .filter(Mission.mission_id == mission_id)
                .first()
            )
        return mission_instance
    except Exception as err:
        capture_exception(err)
        raise


def create_mission_instance(
    robot_id,
    start_timestamp,
    mission_json,
    mission_id=None,
    issues_recorded=None,
    end_timestamp=None,
    schedule_id=None,
    is_deleted=False,
    is_complete=False,
    required_intervention=False,
    success_category=None,
    is_cancelled=False,
    is_scheduled=False,
    analysis_complete=False,
    loop_count=None,
):
    """Creates mission_instance

    :param str(uuid) robot_id: Unique ID for robot
    :param str(uuid) mission_id: Unique ID for mission
    :param str(uuid) schedule_id: Unique ID for schedule
    :param dict mission_json: Dictionay of tasks list with mission name
    :param datatime start_timestamp: Start time for mission execution
    :param datetime end_timestamp: End time for mission completion
    :param boolean is_deleted: Boolean for executed deleted schedules
    :param boolean is_complete: Boolean to check mission status
    :param boolean required_intervention: Boolean to check interventions
    :param boolean is_cancelled: Boolean to check for cancelled missions
    :param boolean is_scheduled: Boolean to check for scheduled missions
    :param dict issues_recorded: Dict for the issues occured during mission
    :param str success_category: String corresponding to mission status
    :return MissionInstance: Row of new MissionInstance
    """
    try:
        new_mission_instance = MissionInstance(
            robot_id,
            start_timestamp,
            mission_json,
            mission_id,
            issues_recorded,
            end_timestamp,
            schedule_id,
            is_deleted,
            is_complete,
            required_intervention,
            success_category,
            is_cancelled,
            is_scheduled,
            analysis_complete,
            loop_count,
        )
        db.session.add(new_mission_instance)
        db.session.flush()
        return new_mission_instance
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def delete_mission_instance(mission_instance_id):
    """Delete mission_instance.

    :param str(uuid) mission_instance_id: Unique ID for mission_instance
    :return bool: True if mission_instance is deleted
    """
    try:
        mission_instance_row = MissionInstance.query.filter(
            MissionInstance.mission_instance_id == mission_instance_id
        ).first()
        if mission_instance_row:
            # Update last_updated_at for corresponding mission_schedules
            schedule_id = mission_instance_row.schedule_id
            if schedule_id:
                mission_schedule = MissionSchedule.query.filter(
                    MissionSchedule.schedule_id == schedule_id
                ).first()
                mission_schedule.last_updated_at = datetime.datetime.utcnow()
            db.session.delete(mission_instance_row)
            db.session.flush()
            return True
        else:
            return False
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def delete_ended_mission_instance(mission_instance_id):
    """Mark mission_instance that already occured as deleted.

    :param str(uuid) mission_instance_id: Unique ID for mission_instance
    :return bool: True if mission_instance is deleted
    """
    try:
        mission_instance_row = MissionInstance.query.filter(
            MissionInstance.mission_instance_id == mission_instance_id
        ).first()
        mission_instance_row.is_deleted = True
        mission_instance_row.schedule_id = None
        mission_instance_row.last_updated_at = datetime.datetime.utcnow()
        db.session.flush()
        return True
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def get_mission_instance(mission_instance_id):
    """Get mission_instance details from mission_instance_id.

    :param str(uuid) mission_instance_id: Unique ID for mission_instance
    :return mission_instance_details: Details of mission_instance
    """
    try:
        mission_instance_row = (
            MissionInstance.query.filter(
                MissionInstance.mission_instance_id == mission_instance_id,
                MissionInstance.is_deleted == False,
            )
            .first()
        )
        if mission_instance_row:
            return mission_instance_row.repr_name()
        else:
            return None
    except Exception as err:
        capture_exception(err)
        raise


def update_mission_instance(data):
    """Update mission_instance.

    :param dict data: Dictionary of updated values for table columns
    :return bool: True if mission_instance is updated
    """
    try:
        mission_instance_row = MissionInstance.query.filter(
            MissionInstance.mission_instance_id == data["mission_instance_id"]
        ).first()
        if mission_instance_row:
            for attribute in data:
                if data[attribute] is not None:
                    setattr(mission_instance_row, attribute, data[attribute])
            mission_instance_row.last_updated_at = datetime.datetime.utcnow()
            # Updating last updated for corresponding mission
            # Update last_updated_at for corresponding mission_schedules
            schedule_id = mission_instance_row.schedule_id
            if schedule_id:
                mission_schedule = MissionSchedule.query.filter(
                    MissionSchedule.schedule_id == schedule_id
                ).first()
                mission_schedule.last_updated_at = datetime.datetime.utcnow()
            db.session.flush()
            return mission_instance_row
        else:
            return None
    except Exception as err:
        capture_exception(err)
        raise


def search_mission_instance(
    page=0,
    per_page=10,
    sort_by="start_timestamp",
    sort_order="asc",
    distinct_field=None,
    filters=None,
):
    """
    Search mission_instance based on filters.

    :param int page: page number of mission_instance
    :param int per_page: number of mission_instance in a page
    :param str sort_by: Ordering parameter
    :param str sort_order: order by ascending or descending
    :param filters : filters for log
    :return status status of the response
    :return data data of the response
    """
    data = []
    out_data = {}
    try:
        column = getattr(MissionInstance, sort_by, None)
        if not column:
            return False, {"Message": "Invalid sort_by Key provided"}
        sorting_order = sort_by + " " + sort_order
        query = MissionInstance.query

        if (
            filters
            and filters.get("start_timestamp", None)
            and filters.get("end_timestamp", None)
        ):
            start_timestamp = filters.get("start_timestamp")
            end_timestamp = filters.get("end_timestamp")
            query = query.filter(
                and_(
                    MissionInstance.start_timestamp >= start_timestamp,
                    MissionInstance.end_timestamp <= end_timestamp,
                )
            )

            filters.pop("start_timestamp")
            filters.pop("end_timestamp")

        status, query = dashboard_services.update_query(
            query, MissionInstance, filters=filters
        )
        if not status:
            return False, query

        if distinct_field:
            field = getattr(MissionInstance, distinct_field, None)
            query = query.distinct(field)

        count = query.count()
        if sorting_order:
            query = query.order_by(text(sorting_order))
        if per_page:
            query = query.limit(per_page)
        if page:
            query = query.offset(per_page * (page - 1))
        query = query.all()
        data = [format_mission_instance(i) for i in query]
        out_data["data"] = data
        out_data["result_count"] = count
        out_data["max_pages"] = math.ceil(count / per_page)
        db.session.flush()
    except Exception as err:
        _logger.exception(err)
        db.session.rollback()
        capture_exception(err)
        return False, {"Message": str(err)}
    return True, out_data


def format_mission_instance(row):
    """Returns dictionary of mission_instance row.

    :param MissionInstance row: Row of MissionInstance model
    :return bool: True if mission_instance is updated
    """
    return {
        "mission_instance_id": str(row.mission_instance_id),
        "robot_id": str(row.robot_id) if row.robot_id else None,
        "mission_id": str(row.mission_id) if row.mission_id else None,
        "schedule_id": str(row.schedule_id) if row.schedule_id else None,
        "issues_recorded": row.issues_recorded,
        "start_timestamp": str(row.start_timestamp),
        "end_timestamp": str(row.end_timestamp) if row.end_timestamp else None,
        "is_deleted": row.is_deleted,
        "is_cancelled": row.is_cancelled,
        "success_category": row.success_category,
        "last_updated_at": str(row.last_updated_at),
        "required_intervention": row.required_intervention,
        "is_complete": row.is_complete,
        "mission_json": row.mission_json,
        "is_scheduled": row.is_scheduled,
        "analysis_complete": row.analysis_complete,
    }


def get_mission_instances_after_timestamp(schedule_id, start_timestamp=None):
    """Returns a list of mission_instances after a certain timestamp.

    If no timestamp is provided, current time in UTC will be used instead.
    :param str(uuid) schedule_id: Unique ID for schedule
    :param str(datetime) start_timestamp: Timestamp used to compare
    :return list mission_instance_list: List of mission_instances
    """
    try:
        if start_timestamp:
            mission_instances = MissionInstance.query.filter(
                MissionInstance.schedule_id == schedule_id,
                MissionInstance.start_timestamp > start_timestamp,
            ).all()
        else:
            mission_instances = MissionInstance.query.filter(
                MissionInstance.schedule_id == schedule_id
            ).all()
        return mission_instances
    except Exception as err:
        capture_exception(err)
        raise


def get_mission_instances_between_timestamp(
    schedule_id,
    start_timestamp=datetime.datetime.utcnow(),
    end_timestamp=datetime.datetime.utcnow() + datetime.timedelta(hours=24),
):
    """Returns a list of mission_instances between two timestamps.

    If no timestamp is provided, start_timestamp will be current time in UTC
    and end_timestamp will be 24 hours from current time in UTC instead.
    :param str(uuid) schedule_id: Unique ID for schedule
    :param str(datetime) start_timestamp: Start timestamp used to compare
    :param str(datetime) end_timestamp: End timestamp used to compare
    :return list mission_instance_list: List of mission_instances
    """
    try:
        mission_instances = MissionInstance.query.filter(
            MissionInstance.schedule_id == schedule_id,
            and_(
                MissionInstance.start_timestamp >= start_timestamp,
                MissionInstance.start_timestamp <= end_timestamp,
            ),
        ).all()
        return mission_instances
    except Exception as err:
        capture_exception(err)
        raise


def update_task_status(data):
    """Updates task status for the mission_instances.

    :param str(uuid) mission_instance_id: Unique ID for mission_instance
    :param list(str) task_status_list: Status of each mission task
    :return dict: Dictionary of updated mission instance row
    """
    try:
        mission_instance_row = get_mission_instance_for_update(data)

        task_status_list = data["task_status_list"]
        new_mission_json = mission_instance_row.mission_json

        if task_status_list is not None and len(new_mission_json["tasks"]) != len(
            task_status_list
        ):
            raise Exception("Length of lists not matching")

        if (
            mission_instance_row.task_last_updated_at
            and mission_instance_row.task_last_updated_at
            > convert_iso_str_to_date_time(data["timestamp"])
        ):
            print("Outdated task update, ignoring")
            return mission_instance_row.repr_name()

        for attribute in data:
            if data[attribute] is not None:
                setattr(mission_instance_row, attribute, data[attribute])
        mission_instance_row.last_updated_at = datetime.datetime.utcnow()
        counter = 0

        # Iterating through task_status_list and updating mission_json
        if task_status_list is not None:
            for task in new_mission_json["tasks"]:
                if "end_time" not in task:
                    # Updating end_time only when task status
                    # is either "completed" or "error" or "cancelled"
                    if task_status_list[counter] in ["completed", "error", "cancelled"]:
                        # Updating current task 'end_time'
                        task["end_time"] = str(data["timestamp"])
                if "start_time" not in task:
                    # Updating start_time only when task status
                    # is "running"
                    if task_status_list[counter] == "running":
                        task["start_time"] = str(data["timestamp"])

                if "start_time" in task and task_status_list[counter] == "idling":
                    # Updating end_time for skipped mission tasks
                    task["status"] = "skipped"
                    if "end_time" not in task:
                        task["end_time"] = str(data["timestamp"])
                else:
                    task["status"] = task_status_list[counter]
                counter += 1
            mission_instance_row.mission_json = new_mission_json
            mission_instance_row.task_last_updated_at = str(data["timestamp"])
            # Establishes a change event in the attribute of the instance
            flag_modified(mission_instance_row, "mission_json")

        db.session.flush()
        return mission_instance_row.repr_name()
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def get_mission_instance_for_update(data, retry=1):
    """THIS QUERY USES ROW LEVEL LOCKING TO UPDATE
    MISSION TASKS WITHOUT LOST UPDATE PROBLEM
    THIS WILL LOCK READ/WRITE FOR THE SPECIFIC ROW
    AND WILL ONLY BE RELEASED AFTER SUCCESSFUL COMMIT/ROLLBACK
    """
    try:
        mission_instance_row = (
            MissionInstance.query.filter(
                MissionInstance.mission_instance_id == data["mission_instance_id"]
            )
            .with_for_update()
            .first()
        )

        if mission_instance_row is None:
            raise Exception("MissionInstance not found")
        return mission_instance_row

    except TimeoutError:
        if retry == MISSION_TASK_UPDATE_MAX_RETRY:
            raise
        return get_mission_instance_for_update(data, retry + 1)


def update_mission_instances_from_mission(mission_json, mission_id):
    """Updates mission_json column of mission instance.

    :param dict mission_json: mission_json to be updated
    :param str(uuid) mission_id: Unique ID for mission
    :return list(dict): List of updated mission_instances
    """
    try:
        # Get all mission instances with start_timestamp > current time in UTC
        # using mission_id
        mission_instances = MissionInstance.query.filter(
            MissionInstance.mission_id == mission_id,
            MissionInstance.is_deleted == False,
            MissionInstance.is_cancelled == False,
            MissionInstance.start_timestamp > datetime.datetime.utcnow(),
        ).all()

        # Update the mission_json of these mission instances
        for mission_instance in mission_instances:
            mission_instance.mission_json = mission_json
            mission_instance.last_updated_at = datetime.datetime.utcnow()

        # Flush the updates to DB
        db.session.flush()
        return [mission_instance.repr_name() for mission_instance in mission_instances]
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def get_mission_metrics(
    start_date=None,
    end_date=None,
    robot_id_list=None,
    property_id_list=None,
    is_scheduled=None,
):
    """get mission instance data

    :param str start_date: start datetime
    :param str end_date: end datetime
    :param list(str) robot_id_list: list of robot id
    :param list(str) property_id_list: list of property id
    :param boolean is_scheduled: true for filter only scheduled mission data
    :return list(dict) mission_instance_data: List of mission instances
    """
    try:
        query = MissionInstance.query.join(
            Robot, Robot.robot_id == MissionInstance.robot_id
        ).join(Mission, Mission.mission_id == MissionInstance.mission_id)

        if robot_id_list is not None:
            robot_id_set = set(robot_id_list)
            query = query.filter(MissionInstance.robot_id.in_(robot_id_set))
        if is_scheduled is not None:
            query = query.filter(MissionInstance.is_scheduled == is_scheduled)
        if property_id_list is not None:
            property_id_set = set(property_id_list)
            query = query.join(Property).filter(
                Property.property_id.in_(property_id_set)
            )
        query = query.filter(
            MissionInstance.start_timestamp >= start_date,
            MissionInstance.start_timestamp <= end_date,
            MissionInstance.is_complete == True,
        ).order_by(MissionInstance.start_timestamp)

        mission_instance_data = query.all()

        return [
            mission_instance.repr_name() for mission_instance in mission_instance_data
        ]
    except Exception as err:
        capture_exception(err)
        raise
