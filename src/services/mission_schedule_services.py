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
from src.services import mission_services
import datetime
from croniter import croniter
import logging

_logger = logging.getLogger(__name__)

daily_limits = {"comment": 5, "like": 5, "clickAds": 350}


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
    event_type = random.choice(["comment", "like", "clickAds"])
    claims = get_jwt_claims()
    current_user_id = claims["user_id"]
    profile_id_receiver = get_profile_with_event_count_below_limit(
        event_type
    )  # user receiver
    if profile_id_receiver:
        # Find a unique interaction partner from current user profiles
        days_limit = calculate_days_for_unique_interactions(event_type)
        # user giver
        unique_partner_id = find_unique_interaction_partner(
            profile_id_receiver, event_type, days_limit, current_user_id
        )
        if unique_partner_id:
            tasks = Task.query.filter(Task.tasks_name == event_type).first()
            if tasks:
                mission_should_start.append(
                    {
                        "schedule_id": "",
                        "profile_id": unique_partner_id,
                        "profile_id_receiver": profile_id_receiver,
                        "mission_id": "",
                        "schedule_json": "",
                        "start_timestamp": datetime.datetime.now().strftime(
                            "%d-%m-%Y %H:%M"
                        ),
                        "tasks": [
                            {
                                "mission_id": "",
                                "tasks_id": tasks.tasks_id,
                                "tasks": {
                                    "tasks_id": tasks.tasks_id,
                                    "tasks_name": event_type,
                                    "tasks_json": None,
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
        start_date = datetime.datetime.now() - datetime.timedelta(
            hours=int(days_limit * 24)
        )
    else:
        start_date = datetime.datetime.now() - datetime.timedelta(days=int(days_limit))

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
            db.func.date(Events.created_at) == datetime.datetime.now().date(),
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
            Events.event_type == "clickAds",
            db.func.date(Events.created_at) == datetime.datetime.now().date(),
        )
        .group_by(Events.profile_id_interact)
        .subquery()
    )

    # Query to find a profile that has not interacted, not reached the daily limit,
    # and has the lowest number of clicks
    account = (
        Profiles.query.outerjoin(
            clicks_count_subquery,
            Profiles.profile_id == clicks_count_subquery.c.profile_id_interact,
        )
        .filter(
            Profiles.owner == current_user_id,
            Profiles.profile_id != profile_receiver,
            ~Profiles.profile_id.in_(interacted_subquery),
            ~Profiles.profile_id.in_(reached_limit_subquery),
            Profiles.main_account.isnot(True)
            if event_type in ["like", "comment"]
            else True,
        )
        .order_by(clicks_count_subquery.c.clicks_count.asc(), func.random())
        .first()
    )

    return account.profile_id if account else None


# Function to calculate days for unique interactions
def calculate_days_for_unique_interactions(event_type):
    # get total verify accounts
    total_accounts = Profiles.query.filter(
        Profiles.profile_data.isnot(None),
        cast(Profiles.profile_data["verify"], Text) == "true",
    ).count()
    unique_interactions_per_account = total_accounts - 1

    days_for_comments_likes = unique_interactions_per_account / daily_limits["like"]
    days_for_clicks = unique_interactions_per_account / daily_limits["clickAds"]
    if event_type in ["like", "comment"]:
        return days_for_comments_likes
    return days_for_clicks


def get_profile_with_event_count_below_limit(event_type):
    # Get today's date
    today = datetime.datetime.now().date()

    # Subquery to count the event type for each profile for today
    event_count_subquery = (
        db.session.query(Events.profile_id, db.func.count().label("event_count"))
        .filter(
            Events.event_type == event_type,
            Events.issue == "OK",
            db.func.date(Events.created_at) == today,  # Filter for today's events
        )
        .group_by(Events.profile_id)
        .subquery()
    )

    # Query to find a profile with event count below the specified limit for today
    # or profiles without event records
    profile = (
        db.session.query(Profiles.profile_id)
        .outerjoin(
            event_count_subquery,
            Profiles.profile_id == event_count_subquery.c.profile_id,
        )
        .filter(
            # Check if event count is below the limit or if there's no event record
            or_(
                event_count_subquery.c.event_count < daily_limits[event_type],
                event_count_subquery.c.event_count.is_(None),
            ),
            Profiles.profile_data.isnot(None),
            cast(Profiles.profile_data["verify"], Text) == "true",
        )
        .order_by(func.random())
        .first()
    )

    return profile.profile_id if profile else None
