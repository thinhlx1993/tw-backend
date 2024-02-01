# mission_schedule_services.py
import random

from flask_jwt_extended import get_jwt_claims
from sqlalchemy import func, cast, or_, Numeric, Text

from src import db
from src.models import (
    MissionSchedule,
    User,
    MissionTask,
    Mission,
    Task,
    Events,
    Profiles,
)
from src.services import mission_services, user_services
import datetime
from croniter import croniter
import logging

_logger = logging.getLogger(__name__)

daily_limits = {"clickAds": 350}


def should_start_job(cron_expression):
    try:
        if not cron_expression:
            return False
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
    """
    {
      schedule_id: '8f74ef78-52ec-46ff-b88a-d93bd1ae9ea5',
      group_id: null,
      profile_id: 'c8a1754f-3769-4816-9c61-f791d7bbddab',
      mission_id: '29868e59-538a-48f9-8673-03ffaf8622df',
      schedule_json: { cron: '', loop_count: 1 },
      start_timestamp: '26-01-2024 08:22',
      tasks: [
        {
          mission_id: '29868e59-538a-48f9-8673-03ffaf8622df',
          tasks_id: '7cc3d468-76fa-4167-aab2-2e37702f3846',
          tasks: {
               mission_id: 'db437f17-f911-40bf-b4e1-db920a5ac787',
               tasks_id: '7cc3d468-76fa-4167-aab2-2e37702f3846',
               tasks: {
                   tasks_id: '7cc3d468-76fa-4167-aab2-2e37702f3846',
                   tasks_name: 'Check follow',
                   tasks_json: null
           }
         }
        }
      ]
    }
    """
    user_info = User.query.filter_by(username=username).first()
    if not user_info:
        return []

    user_id = user_info.user_id

    mission_should_start = []
    mission_force_start = []
    missions = mission_services.get_missions_by_user_id(user_id)
    for mission in missions:
        mission_json = mission.get("mission_json")
        cron_job = mission_json.get("cron")
        if should_start_job(cron_job) or mission["force_start"]:
            mission_schedule = mission["mission_schedule"]
            mission_tasks = mission["mission_tasks"]
            for item in mission_schedule:
                item["tasks"] = mission_tasks
            mission_should_start.extend(mission_schedule)
            mission_force_start.append(mission["mission_id"])

    for mission_id in mission_force_start:
        mission_services.set_force_start_false(mission_id)
    """
    Get tasks for clickAds, comment, like
    """
    event_type = random.choice(list(daily_limits.keys()))
    claims = get_jwt_claims()
    current_user_id = claims["user_id"]

    # user should be online within 5 minutes
    profile_id_receiver = get_profile_with_event_count_below_limit(event_type)

    # Not found any user receiver
    if not profile_id_receiver:
        return mission_should_start

    # Find a unique interaction partner from current user profiles
    days_limit = calculate_days_for_unique_interactions(event_type)
    # user giver
    unique_partner_id = find_unique_interaction_partner(
        profile_id_receiver, event_type, days_limit, current_user_id
    )
    if not unique_partner_id:
        return mission_should_start

    tasks = Task.query.filter(Task.tasks_name == event_type).first()
    if tasks:
        mission_should_start.append(
            {
                "schedule_id": "",
                "profile_id": unique_partner_id,
                "profile_id_receiver": profile_id_receiver,
                "mission_id": "",
                "schedule_json": "",
                "start_timestamp": datetime.datetime.utcnow().strftime(
                    "%d-%m-%Y %H:%M"
                ),
                "tasks": [
                    {
                        "mission_id": "",
                        "tasks_id": tasks.tasks_id,
                        "tasks": {
                            "tasks_id": tasks.tasks_id,
                            "tasks_name": event_type,
                            "tasks_json": tasks.tasks_json,
                        },
                    }
                ],
            }
        )
    return mission_should_start


# Function to find a unique interaction partner
def find_unique_interaction_partner(
    profile_receiver, event_type, days_limit, current_user_id
):
    # Calculate the start date based on days_limit
    if days_limit < 1:
        start_date = datetime.datetime.utcnow() - datetime.timedelta(
            hours=int(days_limit * 24)
        )
    else:
        start_date = datetime.datetime.utcnow() - datetime.timedelta(
            days=int(days_limit)
        )

    # Subquery to find profiles that have already interacted with the given profile
    interacted_subquery = db.session.query(Events.profile_id_interact).filter(
        Events.profile_id == profile_receiver,
        Events.event_type == event_type,
        db.func.date(Events.created_at) >= start_date,
    )

    # Subquery to find profiles that have reached their daily limit for the interaction type
    reached_limit_subquery = (
        db.session.query(Events.profile_id)
        .filter(
            Events.event_type == event_type,
            db.func.date(Events.created_at) == datetime.datetime.utcnow().date(),
        )
        .group_by(Events.profile_id)
        .having(db.func.count() >= daily_limits[event_type])
    )

    # Subquery to count clicks for each profile
    clicks_count_subquery = (
        db.session.query(
            Events.profile_id_interact, db.func.count().label("clicks_count")
        )
        .filter(
            Events.event_type == event_type,
            db.func.date(Events.created_at) == datetime.datetime.utcnow().date(),
        )
        .group_by(Events.profile_id_interact)
        .subquery()
    )

    # Query to find a profile that has not interacted, not reached the daily limit,
    # and has the lowest number of clicks
    # Query to find the top 10 profiles with the lowest number of clicks
    # Filters for monetizable and verified based on event_type
    # if event_type == "clickAds":
    #     monetizable_filter = cast(Profiles.profile_data["monetizable"], Text) == "false"
    #     additional_filters = (monetizable_filter,)
    # else:
    monetizable_filter = cast(Profiles.profile_data["monetizable"], Text) == "false"
    verified_filter = cast(Profiles.profile_data["verify"], Text) == "true"
    additional_filters = (monetizable_filter, verified_filter)

    top_accounts = (
        Profiles.query.outerjoin(
            clicks_count_subquery,
            Profiles.profile_id == clicks_count_subquery.c.profile_id_interact,
        )
        .filter(
            Profiles.owner == current_user_id,
            Profiles.profile_id != profile_receiver,
            ~Profiles.profile_id.in_(interacted_subquery),
            ~Profiles.profile_id.in_(reached_limit_subquery),
            Profiles.main_profile == False,
            *additional_filters
        )
        .order_by(clicks_count_subquery.c.clicks_count.asc())
        .limit(10)
        .all()
    )

    # Randomly select one account from the top 10
    account = random.choice(top_accounts) if top_accounts else None

    # Retrieve the profile ID of the selected account
    selected_profile_id = account.profile_id if account else None

    return selected_profile_id


# Function to calculate days for unique interactions
def calculate_days_for_unique_interactions(event_type):
    # get total verify accounts
    total_accounts = Profiles.query.filter(
        Profiles.profile_data.isnot(None),
        cast(Profiles.profile_data["verify"], Text) == "true",
    ).count()
    unique_interactions_per_account = total_accounts - 1

    if event_type == "fairInteract":
        days_for_comments_likes = (
            unique_interactions_per_account / daily_limits["fairInteract"]
        )
        return days_for_comments_likes
    if event_type == "clickAds":
        days_for_clicks = unique_interactions_per_account / daily_limits["clickAds"]
        return days_for_clicks
    return 14


def get_profile_with_event_count_below_limit(event_type):
    today = datetime.datetime.utcnow().date()

    event_count_subquery = (
        db.session.query(Events.profile_id, db.func.count().label("event_count"))
        .filter(
            Events.event_type == event_type,
            Events.issue == "OK",
            db.func.date(Events.created_at) == today,
        )
        .group_by(Events.profile_id)
        .subquery()
    )

    # Filters for monetizable and verified based on event_type
    if event_type == "clickAds":
        monetizable_filter = cast(Profiles.profile_data["monetizable"], Text) == "true"
        additional_filters = (monetizable_filter,)
    else:
        monetizable_filter = cast(Profiles.profile_data["monetizable"], Text) == "false"
        verified_filter = cast(Profiles.profile_data["verify"], Text) == "true"
        additional_filters = (monetizable_filter, verified_filter)

    profile = (
        db.session.query(Profiles.profile_id, Profiles.owner)
        .outerjoin(
            event_count_subquery,
            Profiles.profile_id == event_count_subquery.c.profile_id,
        )
        .filter(
            or_(
                event_count_subquery.c.event_count < daily_limits[event_type],
                event_count_subquery.c.event_count.is_(None),
            ),
            Profiles.profile_data.isnot(None),
            *additional_filters
        )
        .order_by(func.random())
        .first()
    )

    if not profile:
        return None

    profile_id = profile.profile_id
    owner = profile.owner
    user_data = user_services.check_user_exists(user_id=owner)
    if not user_data:
        return None

    # find activate node
    last_active_at = user_data.last_active_at
    current_time = datetime.datetime.utcnow()
    time_difference = current_time - last_active_at
    if time_difference > datetime.timedelta(minutes=5):
        return None

    return profile_id
