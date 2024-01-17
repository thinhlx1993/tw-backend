# mission_schedule_services.py
from src import db
from src.models import MissionSchedule, User, MissionTask, Mission, Task
from src.services import mission_services
from sqlalchemy.exc import SQLAlchemyError
import datetime
from croniter import croniter
import logging

_logger = logging.getLogger(__name__)


def should_start_job(cron_expression):
    try:
        # Get the current local time
        now = datetime.datetime.utcnow()

        # Initialize croniter with the cron expression and current time
        iter = croniter(cron_expression, now)

        # Get the next scheduled time from the cron expression
        next_schedule = iter.get_next(datetime.datetime)

        # Check if the current time is close to the next scheduled time
        # Here, a threshold of 1 minute is used
        threshold = datetime.timedelta(minutes=1)
        return abs(next_schedule - now) <= threshold
    except Exception as ex:
        _logger.exception(ex)
        return False


def get_mission_schedule(schedule_id):
    return MissionSchedule.query.get(schedule_id)


def get_user_schedule(username):
    user_info = User.query.filter_by(username=username).first()
    user_id = user_info.user_id

    mission_should_start = []
    mission_force_start = []
    missions = mission_services.get_missions_by_user_id(user_id)
    for mission in missions:
        mission_json = mission.get("mission_json")
        cron_job = mission_json.get("cron")
        if should_start_job(cron_job) or mission['force_start']:
            mission_should_start.append(mission)
            mission_force_start.append(mission["mission_id"])
    for mission_id in mission_force_start:
        mission_services.set_force_start(mission_id)

    return mission_should_start
