"""Services for schedule."""

import datetime
import typing
from uuid import uuid4

from dateutil import parser, tz
from croniter import croniter, croniter_range
from sentry_sdk import capture_exception
from sqlalchemy import or_, and_

from src import db
from src.custom_exceptions import NotFoundException
from src.models import MissionSchedule, Mission
from src.models.mission_instance import MissionInstance
from src.services import mission_instance_services, mission_services
from src.utilities.model_helper import copy_entity_row
from src.utilities.date_util import (
    convert_iso_str_to_date_time,
    get_time_before_n_minutes,
    convert_date_time_to_str,
    convert_str_to_date_time,
    get_time_after_n_minutes,
)


def scheduled_missions_sort(sort_by, sort_order, scheduled_msns):
    """Helper function for /schedule GET sorting feature
        :param str sort_by: The key to sort the data by
        :param str sort_order: The sorting order (asc or desc)
        :param str scheduled_msns: Dictionary of scheduled missions
    """
    sorted_ls = []
    if len(scheduled_msns) == 0:
        return []
    else:
        scheduled_ls = scheduled_msns.get('scheduled_missions') #the list of dict
        if sort_order.lower() == "asc":
            sorted_ls = sorted(scheduled_ls, key=lambda d: d[sort_by])
        else:
            sorted_ls = sorted(scheduled_ls, key=lambda d: d[sort_by], reverse=True)
    return sorted_ls

def create_schedule(
        robot_id, mission_id, timezone, cron=None,
        timestamp=None, loop_count=0, start_timestamp=None):
    """Create Schedule for a mission using cron or timestamp.

    :param str(uuid) robot_id: Unique identifier for robot
    :param str(uuid) mission_id: Unique identifier for mission
    :param str timezone: Timezone for schedule
    :param str cron: Cron expression for schedule
    :param datetime timestamp: Timestamp for schedule
    :param integer loop_count: Looping count for mission in schedule
    :param datetime start_timestamp: After this date the schedule will be available for query or fetching
    :return new_schedule: Newly created schedule
    """
    try:
        # Ensure only one of cron or timestamp are used
        if not cron and not timestamp:
            raise Exception("Cron or timestamp required")
        if cron and timestamp:
            raise Exception("Only one of cron or timestamp can be used")
        # Check timezone validity
        if not tz.gettz(timezone):
            raise Exception("Invalid timezone string")
        # Prepare schedule json
        if cron:
            if not croniter.is_valid(cron):
                raise Exception("Cron expression is not valid")
            schedule_json = {
                "cron": cron,
                "loop_count": loop_count
            }
        if timestamp:
            schedule_json = {
                "timestamp": timestamp,
                "loop_count": loop_count
            }
        # Add schedule to table
        new_schedule = MissionSchedule(
            robot_id, mission_id, schedule_json, timezone)
        if start_timestamp:
            # if not specify, set default now()
            new_schedule.start_timestamp = start_timestamp
        db.session.add(new_schedule)
        db.session.flush()
        return new_schedule
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def update_schedule(
        schedule_id, timezone=None, cron=None,
        timestamp=None, loop_count=None, edit_type=None,
        current_schedule_timestamp=None, start_timestamp=None):
    """Update cron, timestamp or loop_count for a schedule.

    :param str(uuid) schedule_id: Unique identifier for schedule
    :param str timezone: Timezone for schedule
    :param str cron: Cron expression for schedule
    :param datetime timestamp: Timestamp for schedule
    :param integer loop_count: Looping count for mission in schedule
    :param datetime start_timestamp: From this time, the scheduler will enable for query or fetching
    :return bool: True if successful
    """
    from src.v2.dto import ScheduleEditType

    try:
        # Ensure only one of cron or timestamp are used
        if cron and timestamp:
            raise Exception("Only one of cron or timestamp can be used")
        # Check timezone validity
        if timezone:
            if not tz.gettz(timezone):
                raise Exception("Invalid timezone string")
        # Get schedule based on schedule_id
        schedule_details: MissionSchedule = MissionSchedule.query.filter(
            MissionSchedule.schedule_id == schedule_id).first()
        if not schedule_details:
            raise Exception("Schedule does not exists")
        schedule_json = dict(schedule_details.schedule_json)

        if cron:
            if not croniter.is_valid(cron):
                raise Exception("Cron expression is not valid")
            if "timestamp" in schedule_json:
                del schedule_json['timestamp']
            schedule_json['cron'] = cron
            if start_timestamp:
                schedule_details.start_timestamp = start_timestamp

        if timestamp:
            if "cron" in schedule_json:
                del schedule_json['cron']
            schedule_json['timestamp'] = timestamp
        if loop_count:
            schedule_json['loop_count'] = loop_count
        if timezone:
            schedule_details.timezone = timezone

        if edit_type is not None and current_schedule_timestamp is None:
            raise Exception("current_schedule_timestamp is needed for edit_type")
        
        check_schedule_edit_type(timestamp, edit_type)

        timestamp_utc = get_updated_utc_timestamp(
            timezone, cron, timestamp, current_schedule_timestamp
        )

        if edit_type == ScheduleEditType.THIS_EVENT.value:
            delete_existing_mission_instance_and_create_new(
                schedule_id,
                current_schedule_timestamp,
                schedule_details,
                timestamp_utc,
                loop_count,
                schedule_json
            )

        elif edit_type == ScheduleEditType.THIS_EVENT_AND_FOLLOWING_EVENTS.value:
            schedule_details = create_new_schedule_and_update_existing_one(
                current_schedule_timestamp,
                timestamp_utc,
                schedule_details,
                schedule_json
            )

        elif edit_type is None or edit_type == ScheduleEditType.ALL_EVENTS.value:
            update_schedule_and_delete_future_mission_instances(
                schedule_id,
                schedule_details,
                schedule_json
            )
        return True, schedule_details.repr_name()

    except Exception as err:
        capture_exception(err)
        db.session.rollback()
        raise

def check_schedule_edit_type(timestamp: str, edit_type: str):
    """Check whether the edit type is applicable for the schedule type

    :param str timestamp: updated timestamp
    :param str edit_type: type of edit
    :raises Exception
    """
    from src.v2.dto import ScheduleEditType

    if timestamp and edit_type in [
        ScheduleEditType.THIS_EVENT_AND_FOLLOWING_EVENTS.value,
        ScheduleEditType.ALL_EVENTS.value,
    ]:
        raise Exception("Invalid edit type for schedule")


def get_updated_utc_timestamp(
    timezone: str, cron: str, timestamp: str, current_schedule_timestamp: str
):
    """Generate utc datetime object for the edited timestamp

    :param str timezone: Timezone of the client
    :param str cron: Cron expression
    :param str timestamp: Timestamp of schedule
    :return datetime: updated datetime
    """
    timestamp_dt = convert_iso_str_to_date_time(timestamp) if timestamp else None
    schedule_timestamp = timestamp_dt or get_schedule_timestamp_from_cron(
        cron, timezone, current_schedule_timestamp
    )
    timestamp_utc = (
        schedule_timestamp.replace(tzinfo=tz.gettz(timezone))
        .astimezone(tz.gettz("UTC"))
        .replace(tzinfo=None)
    )

    return timestamp_utc


def get_schedule_timestamp_from_cron(
    cron: str, timezone: str, current_schedule_timestamp: str
) -> datetime:
    """Get start timestamp from the cron expression

    :param str cron: Cron expression
    :param str timezone: Timezone of client
    :return datetime: cron start timestamp
    """
    local_tz = tz.gettz(timezone)
    schedule_day = (
        convert_iso_str_to_date_time(current_schedule_timestamp).replace(
            tzinfo=local_tz
        )
        if current_schedule_timestamp
        else datetime.datetime.now(tz=local_tz)
    )
    start_of_schedule_day = schedule_day.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    iter = croniter(cron, start_of_schedule_day)
    return iter.get_next(datetime.datetime)



def create_new_schedule_and_update_existing_one(
    current_timestamp: str,
    updated_timestamp: datetime.datetime,
    schedule_details: MissionSchedule,
    schedule_json: typing.Dict[str, typing.Any],
)-> MissionSchedule:
    """Create new schedule with updated values and 
    edit existing schedule to end before the new one

    :param str current_timestamp: utc timestamp of the edited schedule
    :param datetime updated_timestamp: updated timestamp
    :param MissionSchedule schedule_details: _description_
    :param dict[str, Any] schedule_json: updated schedule info
    :return MissionSchedule: new schedule details
    """
    new_schedule: MissionSchedule = copy_entity_row(
        MissionSchedule, schedule_details, None, None, None, None
    )
    new_schedule.schedule_id = str(uuid4())
    new_schedule.schedule_json = schedule_json
    new_schedule.last_updated_at = datetime.datetime.utcnow()
    new_schedule.start_timestamp = updated_timestamp
    db.session.add(new_schedule)

    # Delete all existing mission instances after current_timestamp
    MissionInstance.query.filter(
        MissionInstance.schedule_id == schedule_details.schedule_id,
        MissionInstance.is_complete == False,
        MissionInstance.start_timestamp >= current_timestamp,
    ).update({"is_deleted": True}, synchronize_session=False)

    time_delta_in_minutes = 1
    # Update existing schedule end time to before the new schedule
    schedule_details.end_timestamp = convert_date_time_to_str(
        get_time_before_n_minutes(updated_timestamp, time_delta_in_minutes),
        "%Y-%m-%dT%H:%M:%S",
    )
    db.session.flush()
    return new_schedule

def delete_existing_mission_instance_and_create_new(
    schedule_id: str,
    current_timestamp: str,
    schedule_details: MissionSchedule,
    updated_timestamp: datetime,
    loop_count: int,
    schedule_json: typing.Dict[str, typing.Any],
):
    """Delete the existing mission instance for the sepcified 
    timestamp and create new one with updated values

    :param str schedule_id: id of the schedule
    :param str current_timestamp: utc timestamp of the edited schedule
    :param MissionSchedule schedule_details: schedule details
    :param datetime updated_timestamp: updated timestamp of the schedule
    """
    # If not a cron we can directly edit the schedule
    if "timestamp" in schedule_details.schedule_json:
        schedule_details.schedule_json = schedule_json
        schedule_details.last_updated_at = datetime.datetime.utcnow()
        db.session.flush()
        return

    # Delete existing mission instance
    timestamp_dt = convert_str_to_date_time(current_timestamp, "%Y-%m-%dT%H:%M:%S")
    MissionInstance.query.filter(
        MissionInstance.schedule_id == schedule_id,
        MissionInstance.is_complete == False,
        MissionInstance.start_timestamp == timestamp_dt,
    ).update({"is_deleted": True}, synchronize_session=False)

    mission: Mission = Mission.query.get(schedule_details.mission_id)

    # create new mission instance
    mission_instance_services.create_mission_instance(
        robot_id=schedule_details.robot_id,
        schedule_id=schedule_details.schedule_id,
        mission_id=schedule_details.mission_id,
        start_timestamp=updated_timestamp,
        mission_json=mission.mission_json,
        is_scheduled=True,
        loop_count=loop_count,
    )


def update_schedule_and_delete_future_mission_instances(
    schedule_id: str,
    schedule_details: MissionSchedule,
    schedule_json: typing.Dict[str, typing.Any],
):
    """Update existing schedule and delete all the future mission instances

    :param str schedule_id: id of the edited schedule
    :param MissionSchedule schedule_details: schedule details
    :param dict[str, Any] schedule_json: updated schedule info
    """
    schedule_details.schedule_json = schedule_json
    schedule_details.last_updated_at = datetime.datetime.utcnow()
    # Remove mission instances that are not completed yet
    # and have a start_timestamp greater than current time in UTC
    # So that ongoing mission will not be deleted.

    MissionInstance.query.filter(
        MissionInstance.schedule_id == schedule_id,
        MissionInstance.is_complete == False,
        MissionInstance.start_timestamp > datetime.datetime.utcnow(),
    ).delete()

    db.session.flush()



def get_scheduled_missions(
        robot_id, start_time, end_time, create_mission_instance=False):
    from src.v2.dto.schedule_type import ScheduleType  # import datatype
    """Get all scheduled missions for a robot within datetime range.

    :param str(uuid) robot_id: Unique Identifier for robot
    :param datetime start_time: Start time for schedule
    :param datetime end_time: End time for schedule
    return dict schedule_details: Dict containing all schedule details
    """
    try:
        # Check if schedule exists for robot
        schedule_list = (
            MissionSchedule.query.filter(
                MissionSchedule.robot_id == robot_id,
                or_(
                    MissionSchedule.end_timestamp == None,
                    # end_timestamp > start_time - 24 hr
                    MissionSchedule.end_timestamp > get_time_after_n_minutes(start_time, 24 * 60),
                ),
                or_(
                    MissionSchedule.start_timestamp < start_time,
                    MissionSchedule.start_timestamp.between(start_time, end_time),
                )
            )
            .join(Mission, MissionSchedule.mission_id == Mission.mission_id)
            .order_by(MissionSchedule.last_updated_at.desc())
            .all()
        )
        if not schedule_list:
            # return empty list if no schedules are present
            return []
        schedule_list = [schedule.repr_schedule_with_mission() for
            schedule in schedule_list]
        scheduled_missions = []
        # Initialize UTC timezone for conversion
        utc_tz = tz.gettz("UTC")
        for schedule in schedule_list:
            # Get a list of all mission instances for this schedule
            # between min(current time in UTC and start_time)
            # and max((current time + 24hrs in UTC) and end_time)
            mission_instances = (
                mission_instance_services
                .get_mission_instances_between_timestamp(
                    schedule['schedule_id'],
                    start_timestamp=min(
                        start_time,
                        datetime.datetime.utcnow()),
                    end_timestamp=max(
                        end_time,
                        datetime.datetime.utcnow()
                        + datetime.timedelta(hours=24))))
            for mission_instance in mission_instances:
                # if mission instance is not deleted and is within start-end
                # time, add to list of scheduled mission to return
                if (not mission_instance.is_deleted and
                        not mission_instance.is_cancelled and
                        start_time <= mission_instance.start_timestamp
                        <= end_time):
                    scheduled_missions.append({
                        "timestamp": str(
                            mission_instance.start_timestamp.isoformat()),
                        "mission_id": str(schedule['mission_id']),
                        "schedule_id": str(schedule['schedule_id']),
                        "loop_count": str(
                            mission_instance.loop_count or
                            schedule['schedule_json']['loop_count']),
                        "timezone": schedule['timezone'],
                        "mission_name": str(schedule['mission_name']),
                        "schedule_type": ScheduleType.NON_REPEATING.value,
                        "mission_instance_id" : str(
                            mission_instance.mission_instance_id)
                    })
            # Initialize timezone for schedule
            schedule_tz = tz.gettz(schedule['timezone'])
            if "timestamp" in schedule['schedule_json']:
                # Confirm that timestamp is within time range
                timestamp = parser.parse(
                    schedule['schedule_json']['timestamp'],
                    ignoretz=True)
                # Converting from local timezone time to UTC to TZ naive
                timestamp = timestamp.replace(
                    tzinfo=schedule_tz).astimezone(
                    utc_tz).replace(tzinfo=None)

                new_mission_instance = None
                mission_instance_at_timestamp = (
                    mission_instance_services
                    .get_mission_instance_from_timestamp_and_schedule_id(
                        mission_id=schedule["mission_id"],
                        schedule_id=False, timestamp=timestamp))
                # If create_mission_instance flag is True, timestamp is
                # within the next 24hrs in UTC, and mission instance
                # does not exist, create mission instance.
                if (create_mission_instance and datetime.datetime.utcnow()
                        <= timestamp
                        <= datetime.datetime.utcnow()
                        + datetime.timedelta(hours=24) and
                        timestamp not in
                        [mission_instance.start_timestamp for
                        mission_instance in mission_instances] and not
                        mission_instance_at_timestamp):
                    # Get mission details required to create mission instance
                    mission_details = mission_services.get_mission(
                        schedule['mission_id'])
                    new_mission_instance = (
                        mission_instance_services
                        .create_mission_instance(
                            robot_id=robot_id,
                            mission_id=schedule['mission_id'],
                            start_timestamp=timestamp,
                            mission_json=mission_details['mission_json'],
                            issues_recorded=None,
                            end_timestamp=None,
                            schedule_id=schedule['schedule_id'],
                            is_deleted=False,
                            is_complete=False,
                            required_intervention=False,
                            success_category=None,
                            is_cancelled=False,
                            is_scheduled=True))
                # if timestamp is within start-end time, does not
                # match start_timestamp of any existing mission instance,
                # add to list of scheduled missions to return
                if (start_time <= timestamp <= end_time and
                        timestamp not in
                        [mission_instance.start_timestamp for
                        mission_instance in mission_instances] and
                        not mission_instance_at_timestamp):
                    scheduled_missions.append({
                        "timestamp": str(timestamp.isoformat()),
                        "mission_id": str(schedule['mission_id']),
                        "schedule_id": str(schedule['schedule_id']),
                        "loop_count": (schedule['schedule_json']
                                               ['loop_count']),
                        "mission_name": str(schedule['mission_name']),
                        "timezone": schedule['timezone'],
                        "schedule_type": ScheduleType.NON_REPEATING.value,
                        "mission_instance_id":
                            (str(new_mission_instance.mission_instance_id)
                                if new_mission_instance else None)
                    })
            if "cron" in schedule['schedule_json']:
                # We run the cron range on a timezone, hence to make up for the
                # offsets, we do -24h on start and +24h on end to ensure we
                # capture all cron instances. This is then converted to UTC and
                # filtered with utc start and utc end
                timezone_start = start_time - datetime.timedelta(hours=24)
                timezone_end = end_time + datetime.timedelta(hours=24)
                start_timestamp = schedule.get('start_timestamp', None)
                timezone_start = timezone_start.replace(
                    tzinfo=utc_tz).astimezone(schedule_tz)
                timezone_end = timezone_end.replace(
                    tzinfo=utc_tz).astimezone(schedule_tz)
                cron_min_start = min(
                    datetime.datetime.utcnow().replace(tzinfo=utc_tz),
                    timezone_start
                )

                # Loop through all timestamps from cron for timezone range
                # between min(current time, timezone_start) and
                # max((current_time + 24hrs), timezone_end)
                for mission_time in croniter_range(
                    max(
                        convert_iso_str_to_date_time(start_timestamp).replace(tzinfo=utc_tz),
                        cron_min_start),
                    max(
                        (datetime.datetime.utcnow()
                        + datetime.timedelta(
                            hours=24)).replace(tzinfo=utc_tz),
                        timezone_end),
                    schedule['schedule_json']['cron']):
                    # Converting timezone time to UTC to TZ naive
                    mission_time = mission_time.replace(
                        tzinfo=schedule_tz).astimezone(utc_tz).replace(
                        tzinfo=None)

                    mission_instance_at_timestamp = (
                        mission_instance_services
                        .get_mission_instance_from_timestamp_and_schedule_id(
                            mission_id=schedule["mission_id"],
                            schedule_id=False, timestamp=mission_time))
                    new_mission_instance = None
                    # Check if already a mission instance available for
                    # the same schedule within the same day. This is mostly
                    # to filter out manually edited repeating schedule for specific day
                    is_mission_instance_already_created = any(
                        mission_time.replace(hour=0, minute=0, second=0)
                        <= mission_instance.start_timestamp
                        <= mission_time.replace(hour=23, minute=59, second=59)
                        for mission_instance in mission_instances
                    )
                    # If mission time is within next 24hrs and mission
                    # time does not match any start_timestamp of
                    # existing mission instances, create mission instance
                    if (create_mission_instance and datetime.datetime.utcnow()
                            <= mission_time
                            <= datetime.datetime.utcnow()
                            + datetime.timedelta(hours=24) and
                            mission_time not in
                            [mission_instance.start_timestamp for
                            mission_instance in mission_instances] and
                            not mission_instance_at_timestamp
                            and not is_mission_instance_already_created
                            ):
                        # Get mission details required to create mission
                        # instance
                        mission_details = mission_services.get_mission(
                            schedule['mission_id'])
                        new_mission_instance = (
                            mission_instance_services
                            .create_mission_instance(
                                robot_id=robot_id,
                                mission_id=schedule['mission_id'],
                                start_timestamp=mission_time,
                                mission_json=(mission_details['mission_json']),
                                issues_recorded=None,
                                end_timestamp=None,
                                schedule_id=schedule['schedule_id'],
                                is_deleted=False,
                                is_complete=False,
                                required_intervention=False,
                                success_category=None,
                                is_cancelled=False,
                                is_scheduled=True))

                    # If mission_time is within start-end time and does not
                    # match the start_timestamp of any existing mission
                    # instances, add to list of scheduled missions to return
                    if (start_time <= mission_time <= end_time and
                            mission_time not in
                            [mission_instance.start_timestamp for
                            mission_instance in mission_instances] and
                            not mission_instance_at_timestamp
                            and not is_mission_instance_already_created
                            ):
                        scheduled_missions.append({
                            "timestamp": str(mission_time.isoformat()),
                            "mission_id": str(schedule['mission_id']),
                            "schedule_id": str(schedule['schedule_id']),
                            "loop_count": (schedule['schedule_json']
                                                   ['loop_count']),
                            "mission_name": str(schedule['mission_name']),
                            "mission_instance_id":
                                (str(new_mission_instance.mission_instance_id)
                                    if new_mission_instance else None),
                            "schedule_type": ScheduleType.REPEATING.value,
                            "cron": schedule['schedule_json']['cron'],
                            "timezone": schedule['timezone'],
                            "start_timestamp": start_timestamp
                        })
        # Prepare list of last_updated values for robot to then select the max
        # value to send
        latest_updated = [schedule['last_updated_at'] for
            schedule in schedule_list]
        schedule_details = {
            "scheduled_missions": scheduled_missions,
            "last_updated_at": str(max(latest_updated))
        }
        return schedule_details
    except Exception as err:
        capture_exception(err)
        raise err


def get_schedule(schedule_id):
    """Get schedule details.

    :param str(uuid) schedule_id: Unique identifier for schedule
    :return schedule_details: Details of schedule
    """
    try:
        schedule_details = MissionSchedule.query.filter(
            MissionSchedule.schedule_id == schedule_id).first()
        if schedule_details:
            return schedule_details.repr_name()
        else:
            return None
    except Exception as err:
        capture_exception(err)
        raise


def delete_schedule(schedule_id, schedule_delete_input={}):
    """Delete a schedule.

    :param schedule_id: Unique ID for each schedule
    :return bool: True if successful
    """
    from src.v2.dto import ScheduleDeleteType

    try:
        schedule = MissionSchedule.query.filter(
            MissionSchedule.schedule_id == schedule_id
        ).first()
        if not schedule:
            raise NotFoundException("Schedule does not exists")

        robot_id = str(schedule.robot_id)
        delete_type = schedule_delete_input.get("delete_type", None)
        # UTC timestamp of edited schedule
        current_schedule_timestamp = schedule_delete_input.get(
            "current_schedule_timestamp", None
        )
        # Parsed UTC timestamp of edited schedule
        timestamp_dt = (
            convert_iso_str_to_date_time(current_schedule_timestamp)
            if current_schedule_timestamp
            else None
        )

        if delete_type == ScheduleDeleteType.THIS_EVENT.value:
            mark_schedule_instance_as_deleted_at_timestamp(schedule, timestamp_dt)

        elif delete_type == ScheduleDeleteType.THIS_EVENT_AND_FOLLOWING_EVENTS.value:
            update_schedule_and_delete_future_instances(schedule, timestamp_dt)

        elif delete_type is None or delete_type == ScheduleDeleteType.ALL_EVENTS.value:
            delete_schedule_and_instances(schedule, robot_id)

        return True
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def update_schedule_and_delete_future_instances(
    schedule: MissionSchedule, timestamp_dt: datetime.datetime
):
    """Mark future mission instance as deleted and update schedule end timestamp

    :param MissionSchedule schedule: Schedule that is being updated
    :param datetime.datetime timestamp_dt: Timestamp of the schedule 
    that needs to be deleted
    """
    MissionInstance.query.filter(
        MissionInstance.schedule_id == schedule.schedule_id,
        MissionInstance.is_complete == False,
        MissionInstance.start_timestamp >= timestamp_dt,
    ).update({"is_deleted": True}, synchronize_session=False)
    schedule.end_timestamp = timestamp_dt
    db.session.flush()


def mark_schedule_instance_as_deleted_at_timestamp(
    schedule: MissionSchedule, timestamp_dt: datetime.datetime
):
    """Mark mission instance as deleted if exist else create
    one and marked as deleted for the specified timestamp

    :param MissionSchedule schedule: Schedule that is being updated
    :param datetime.datetime timestamp_dt: Timestamp of the schedule 
    that needs to be deleted
    """
    mission_instance = MissionInstance.query.filter(
        MissionInstance.schedule_id == schedule.schedule_id,
        MissionInstance.is_complete == False,
        MissionInstance.start_timestamp == timestamp_dt,
    ).first()

    if not mission_instance:
        mission: Mission = Mission.query.get(schedule.mission_id)
        mission_instance = mission_instance_services.create_mission_instance(
            robot_id=schedule.robot_id,
            schedule_id=schedule.schedule_id,
            mission_id=schedule.mission_id,
            start_timestamp=timestamp_dt,
            mission_json=mission.mission_json,
            is_scheduled=True,
            loop_count=schedule.schedule_json.get("loop_count"),
        )
        
    mission_instance.is_deleted = True

    db.session.flush()


def delete_schedule_and_instances(schedule: MissionSchedule, robot_id: str):
    """Delete all instance and delete schedule

    :param str schedule_id: id of the schedule being updated
    :param str robot_id: id of the robot
    """
    schedule.deleted_at = datetime.datetime.now()

    # Delete all mission instances
    # This will fail if mission is started and already generated alerts
    MissionInstance.query.filter(
        MissionInstance.schedule_id == schedule.schedule_id,
        MissionInstance.start_timestamp >= datetime.datetime.utcnow()
    ).delete(synchronize_session=False)

    # Update last_updated_at for robot
    last_schedule_row = MissionSchedule.query.filter(
        MissionSchedule.robot_id == robot_id
    ).first()

    if last_schedule_row:
        last_schedule_row.last_updated_at = datetime.datetime.utcnow()
    db.session.flush()



def get_latest_timestamp(robot_id):
    """Get latest last_updated_at for robot.

    :param str(uuid) robot_id: Unique Identifier for robot
    :return str(datetime): Latest updated timestamp
    """
    try:
        # Check if robot_id is invalid
        robot_exists = Robot.query.filter(
            Robot.robot_id == robot_id).first()
        if not robot_exists:
            raise Exception("Invalid robot_id")
        # Check if schedule exists for robot
        schedule_list = MissionSchedule.query.filter(
            MissionSchedule.robot_id == robot_id).all()
        if not schedule_list:
            return ""
        schedule_list = [schedule.repr_name() for schedule in schedule_list]
        latest_updated = [schedule['last_updated_at'] for
            schedule in schedule_list]
        return max(latest_updated)
    except Exception as err:
        capture_exception(err)
        raise


def get_schedule_list_from_mission_id(mission_id):
    """Get a list of schedules from a mission_id

    :param str(uuid) mission_id: Unique ID for a mission
    :return schedule_list: list of schedules"""
    try:
        schedule_list = MissionSchedule.query.filter(
            MissionSchedule.mission_id == mission_id).all()
        return schedule_list
    except Exception as err:
        capture_exception(err)
        raise

def get_schedule_list(mission_id, schedule_timestamp, schedule_cron):
    """Get a list of schedules with mission_id, timestamp or cron

    :param str(uuid) mission_id: Unique ID for a mission
    :param str(datetime) schedule_timestamp: timestamp for the schedules
    :param str(cron exp) schedule_cron: cron expression for the cron schedules
    :return schedule_list: list of schedules"""
    try:
        schedule_list = MissionSchedule.query.filter(
            MissionSchedule.mission_id == mission_id).all()
    except Exception as err:
        capture_exception(err)
        raise

    try:
        schedule_json_list = []
        for schedule in schedule_list:
            schedule_data = schedule.repr_name()
            if schedule_timestamp:
                if ('timestamp' in schedule_data['schedule_json'] and 
                        schedule_data['schedule_json']['timestamp'] == 
                        schedule_timestamp):
                    schedule_json_list.append(schedule_data)
            
            elif schedule_cron:
                if ('cron' in schedule_data['schedule_json'] and 
                        schedule_data['schedule_json']['cron'] == 
                        schedule_cron):
                    schedule_json_list.append(schedule_data)
            
            elif not schedule_cron and not schedule_timestamp:
                schedule_json_list.append(schedule_data)
        
        return schedule_json_list
    except Exception as err:
        capture_exception(err)
        raise
