# mission_schedule_services.py
import random
import pytz
from flask_jwt_extended import get_jwt_claims
from sqlalchemy import func, cast, or_, Text

from src import db, app
from src.models import (
    MissionSchedule,
    User,
    Task,
    Events,
    Profiles,
)
from src.services import mission_services
import datetime
from croniter import croniter
import logging

from src.services.migration_services import get_readonly_session

_logger = logging.getLogger(__name__)

daily_limits = {"clickAds": 400}


# 30% clicks


def should_start_job(cron_expression):
    try:
        if not cron_expression:
            return False
        # Get the current local time
        # now = datetime.datetime.now()
        tz_ho_chi_minh = pytz.timezone("Asia/Ho_Chi_Minh")
        now = datetime.datetime.now(tz_ho_chi_minh)

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
    return MissionSchedule.query.execution_options(
        bind=db.get_engine(app, bind="readonly")
    ).get(schedule_id)


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
    """
    {
        "mission_id": self.mission_id,
        "mission_name": self.mission_name,
        "status": self.status,
        "user_id": self.user_id,
        "mission_json": self.mission_json,
        "force_start": self.force_start,
        "group_id": self.group_id,
        "created_at": self.created_at.isoformat() if self.created_at else None,
        "mission_schedule": [item.repr_name() for item in self.mission_schedule],
        "mission_tasks": [item.repr_name() for item in self.mission_tasks],
    }
    """
    claims = get_jwt_claims()
    current_user_id = claims["user_id"]

    # check follow every morning 4:30 AM
    if should_start_job("30 4 * * *") or should_start_job("30 16 * * *"):
        profiles = Profiles.query.filter(Profiles.owner == current_user_id).all()
        default_missions = []
        for profile in profiles:
            default_missions.append(
                {
                    "profile_id": profile.profile_id,
                    "profile_id_receiver": profile.profile_id,
                    "start_timestamp": datetime.datetime.utcnow().strftime(
                        "%d-%m-%Y %H:%M"
                    ),
                    "tasks": [
                        {
                            "tasks_id": "7cc3d468-76fa-4167-aab2-2e37702f3846",
                            "tasks": {
                                "tasks_id": "7cc3d468-76fa-4167-aab2-2e37702f3846",
                                "tasks_name": "Check follow",
                                "tasks_json": None,
                            },
                        }
                    ],
                }
            )
        return default_missions

    with get_readonly_session() as readonly_session:
        mission_should_start = []
        mission_force_start = []
        missions = mission_services.get_missions_by_user_id(
            current_user_id, readonly_session
        )
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

        if mission_should_start:
            return mission_should_start

        """
        Get tasks for clickAds, comment, like
        """
        event_type = random.choice(list(daily_limits.keys()))

        # user should be online within 5 minutes
        profile_ids_receiver = get_profile_with_event_count_below_limit_v2(
            event_type, readonly_session
        )

        # Not found any user receiver
        if not profile_ids_receiver:
            return mission_should_start

        # Find a unique interaction partner from current user profiles
        days_limit = calculate_days_for_unique_interactions(
            event_type, readonly_session
        )

        partner_ids = []
        # create missions
        for profile_id_receiver in profile_ids_receiver:
            # user giver
            unique_partner_id = find_unique_interaction_partner_v2(
                profile_id_receiver,
                event_type,
                days_limit,
                current_user_id,
                readonly_session,
                partner_ids,
            )
            if not unique_partner_id:
                continue
            partner_ids.append(unique_partner_id)

            tasks = (
                readonly_session.query(Task)
                .filter(Task.tasks_name == event_type)
                .first()
            )
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
    interacted_subquery = (
        db.session.query(Events.profile_id_interact)
        .distinct()
        .filter(
            Events.profile_id == profile_receiver,
            Events.event_type == event_type,
            Events.issue == "OK",
            db.func.date(Events.created_at) >= start_date,
        )
        .execution_options(bind=db.get_engine(app, bind="readonly"))
    )

    # Subquery to find profiles that have reached their daily limit for the interaction type
    reached_limit_subquery = (
        db.session.query(Events.profile_id)
        .filter(
            Events.issue == "OK",
            Events.event_type == event_type,
            db.func.date(Events.created_at) == datetime.datetime.utcnow().date(),
        )
        .group_by(Events.profile_id)
        .having(db.func.count() >= daily_limits[event_type])
        .execution_options(bind=db.get_engine(app, bind="readonly"))
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
        .execution_options(bind=db.get_engine(app, bind="readonly"))
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
            Profiles.main_profile == False,
            *additional_filters
        )
        .order_by(func.random())
        .execution_options(bind=db.get_engine(app, bind="readonly"))
        .first()
    )

    # Randomly select one account from the top 10
    # account = random.choice(top_accounts) if top_accounts else None

    # Retrieve the profile ID of the selected account
    selected_profile_id = account.profile_id if account else None

    return selected_profile_id


def find_unique_interaction_partner_v2(
    profile_receiver,
    event_type,
    days_limit,
    current_user_id,
    readonly_session,
    partner_ids,
):
    # Calculate the start date based on days_limit
    if days_limit < 1:
        start_date = datetime.datetime.utcnow() - datetime.timedelta(
            hours=int(days_limit * 24)
        )
    else:
        start_date = datetime.datetime.utcnow() - datetime.timedelta(days=days_limit)

    # Subquery to find profiles that have already interacted with the given profile
    interacted_subquery = (
        readonly_session.query(Events.profile_id_interact)
        .distinct()
        .filter(
            Events.profile_id == profile_receiver,
            Events.event_type == event_type,
            Events.issue == "OK",
            db.func.date(Events.created_at) >= start_date,
        )
    )

    # monetizable_filter = cast(Profiles.profile_data["monetizable"], Text) == "false"
    # func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
    #     ["NotStarted", 'ERROR']
    # ),
    verified_filter = cast(Profiles.profile_data["verify"], Text) == "true"
    # additional_filters = (verified_filter)

    top_accounts = (
        readonly_session.query(Profiles.profile_id)
        .filter(
            Profiles.owner == current_user_id,
            Profiles.profile_id != profile_receiver,
            ~Profiles.profile_id.in_(interacted_subquery),
            ~Profiles.profile_id.in_(partner_ids),
            Profiles.click_count < daily_limits[event_type],
            Profiles.main_profile == False,
            Profiles.is_disable == False,
            # func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
            #     ["NotStarted", "ERROR", "OK"]
            # ),
            cast(Profiles.profile_data["verify"], Text) == "true",
        )
        .order_by(func.random())
        .limit(5)
        .all()
    )

    # Randomly select one account from the top 10
    account = random.choice(top_accounts) if top_accounts else None

    # Retrieve the profile ID of the selected account
    selected_profile_id = account.profile_id if account else None

    return selected_profile_id


# Function to calculate days for unique interactions
def calculate_days_for_unique_interactions(event_type, readonly_session):
    # get total verify accounts
    # monetizable_filter = cast(Profiles.profile_data["monetizable"], Text) == "false"
    # verified_filter = cast(Profiles.profile_data["verify"], Text) == "true"
    # additional_filters = (monetizable_filter, verified_filter)

    total_accounts = (
        readonly_session.query(Profiles)
        .filter(
            Profiles.profile_data.isnot(None),
            Profiles.main_profile == False,
            Profiles.is_disable == False,
            func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
                ["NotStarted", "ERROR"]
            ),
        )
        .count()
    )
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
    active_cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)

    # Step 1: Query active user IDs
    active_user_ids = (
        db.session.query(User.user_id)
        .filter(User.last_active_at > active_cutoff)
        .execution_options(bind=db.get_engine(app, bind="readonly"))
        .all()
    )
    active_user_ids = [user_id[0] for user_id in active_user_ids]

    # Step 2: Setup the event count subquery
    event_count_subquery = (
        db.session.query(Events.profile_id, db.func.count().label("event_count"))
        .filter(
            Events.event_type == event_type,
            Events.issue == "OK",
            db.func.date(Events.created_at) == today,
        )
        .group_by(Events.profile_id)
        .execution_options(bind=db.get_engine(app, bind="readonly"))
        .subquery()
    )

    # Filters for monetizable and verified based on event_type
    # if event_type == "clickAds":
    #     monetizable_filter = cast(Profiles.profile_data["monetizable"], Text) == "true"
    #     additional_filters = (monetizable_filter,)
    # else:
    #     monetizable_filter = cast(Profiles.profile_data["monetizable"], Text) == "false"
    #     verified_filter = cast(Profiles.profile_data["verify"], Text) == "true"
    #     additional_filters = (monetizable_filter, verified_filter)

    # Step 3: Filter profiles based on event count and active users
    profiles = (
        db.session.query(Profiles.profile_id)
        .outerjoin(
            event_count_subquery,
            Profiles.profile_id == event_count_subquery.c.profile_id,
        )
        .filter(
            Profiles.owner.in_(active_user_ids),  # Filter by active user IDs
            or_(
                event_count_subquery.c.event_count < daily_limits[event_type],
                event_count_subquery.c.event_count.is_(None),
            ),
            Profiles.profile_data.isnot(None),
            func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
                ["NotStarted", "OK"]
            ),
            Profiles.main_profile.is_(True),
        )
        .order_by(func.random())
        .execution_options(bind=db.get_engine(app, bind="readonly"))
        .first()
    )

    # Select a random profile from the filtered list
    # profile = random.choice(profiles) if profiles else None

    if profiles:
        return profiles.profile_id
    else:
        return None


def get_profile_with_event_count_below_limit_v2(event_type, readonly_session):
    """Count direct by click count in profile data"""
    # active_cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)

    # query priority user first
    choose_otp = random.choice([0, 1])
    profiles = []
    if choose_otp == 0:
        active_user_ids = [
            "307aa5f6-b63e-4a6d-a134-f84a96a38256",
            "0c3c328c-752f-4b2d-9884-9e8832915056",
        ]
        # # Step 3: Filter profiles based on event count and active users
        profiles = (
            readonly_session.query(Profiles.profile_id)
            .filter(
                Profiles.owner.in_(active_user_ids),  # Filter by active user IDs
                Profiles.click_count < daily_limits[event_type],
                Profiles.profile_data.isnot(None),
                func.json_extract_path_text(
                    Profiles.profile_data, "account_status"
                ).in_(["AdsEligible", "OK"]),
                Profiles.main_profile.is_(True),
                Profiles.is_disable.is_(False),
            )
            .order_by(func.random())
            .limit(10)
            .all()
        )

    if len(profiles) == 0:
        # Step 1: Query active user IDs
        active_cutoff = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        active_user_ids = (
            db.session.query(User.user_id)
            .filter(User.last_active_at > active_cutoff)
            .all()
        )
        active_user_ids = [user_id[0] for user_id in active_user_ids]

        profiles = (
            readonly_session.query(Profiles.profile_id)
            .filter(
                Profiles.owner.in_(active_user_ids),  # Filter by active user IDs
                Profiles.click_count < daily_limits[event_type],
                Profiles.profile_data.isnot(None),
                func.json_extract_path_text(
                    Profiles.profile_data, "account_status"
                ).in_(["AdsEligible", "OK"]),
                Profiles.main_profile.is_(True),
                Profiles.is_disable.is_(False),
            )
            .order_by(func.random())
            .limit(25)
            .all()
        )

    # Select a random profile from the filtered list
    # profile = random.choice(profiles) if profiles else None

    return [profile.profile_id for profile in profiles]
