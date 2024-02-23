import datetime

from flask_jwt_extended import get_jwt_claims
from src import db, app
from src.models import Mission, MissionSchedule, MissionTask
from src.services import profiles_services, user_services
from src.services.migration_services import get_readonly_session
from src.v1.controllers.utils import generate_crontab_schedule


def get_all_missions(user_id):
    """Retrieve all missions."""
    with get_readonly_session() as readonly_session:
        sorting_order = "created_at desc"
        # Now use this session for querying
        missions = [
            item.repr_name()
            for item in readonly_session.query(Mission)
            .filter(Mission.user_id == user_id)
            .order_by(db.text(sorting_order))
            .all()
        ]

    # for mission in missions:
    #     user_id = mission["user_id"]
    #     if user_id:
    #         user_info = user_services.check_user_exists(user_id=user_id)
    #         mission["username"] = user_info.username

    return missions


def get_missions_by_user_id(user_id, readonly_session):
    """Retrieve all missions. by given user id"""
    missions = [
        item.repr_name()
        for item in readonly_session.query(Mission).filter_by(user_id=user_id).all()
    ]
    return missions


def get_missions_by_id(mission_id):
    """Retrieve all missions. by given user id"""
    with get_readonly_session() as readonly_session:
        mission = readonly_session.query(Mission.mission_id).filter_by(mission_id=mission_id).first()
        return mission


def set_force_start_false(mission_id):
    """Update force start flag into false"""
    mission = Mission.query.filter_by(mission_id=mission_id).first()
    mission.force_start = False
    db.session.flush()


def create_mission(data):
    """Create a new mission.
    {
       "mission_name":"2312312",
       "group_id":"80051754-c58a-4ab1-b29d-45c0e4c66dae",
       "profile_ids":[
          "username"
       ],
       "tasks":[
          "260a439d-0121-48c1-88e0-b09f4bfd780b",
          "f88f499f-e9bc-497f-aecb-88803151c866",
          "57444c37-886b-43f4-96c3-3fe3a38b916e",
          "7cc3d468-76fa-4167-aab2-2e37702f3846",
          "6becebb3-3028-4015-a435-c7fe728b981b",
          "cbcbeed2-abe1-4fba-9e25-8ca468f47014",
          "2a9aad42-7f5b-4b9d-9e1e-82e5af43e77f",
          "e1ad246e-c562-47ea-a8d2-927eb800300a",
          "7fed041c-4669-421a-a0c4-2af421f5743b"
       ],
       "config_profiles": "acb\ndef\nghi",
       "user_id":"a3213c22-c8c5-4e86-aa7c-ec4a08f0a7f9",
       "mission_schedule":[
          "Monday",
          "Tuesday",
          "Thursday",
          "Wednesday",
          "Friday",
          "Saturday",
          "Sunday"
       ],
       "start_date":"2024-01-17T21:56"
    }
    """
    mission_name = data.get("mission_name")
    group_id = data.get("group_id")
    config = data.get("config", "")
    user_id = data.get("user_id")
    if not user_id:
        claims = get_jwt_claims()
        user_id = claims["user_id"]
    new_mission = Mission(mission_name, group_id, user_id)
    new_mission.created_at = datetime.datetime.utcnow()
    db.session.add(new_mission)
    db.session.flush()  # save missions

    mission_schedule = data.get("mission_schedule", None)
    start_date = data.get("start_date", None)
    if not mission_schedule and not start_date:
        cron = ""
    else:
        cron = generate_crontab_schedule(start_date, mission_schedule)
    schedule_json = {"cron": cron, "loop_count": 1}
    new_mission.mission_json = schedule_json
    new_mission.status = "unknown"

    if not data.get("profile_ids", ""):
        # fetch by from group_id
        profiles_selected = profiles_services.get_profile_by_user(user_id=user_id)
    else:
        profile_ids = data.get("profile_ids", "").split("\n")
        """Check if profile_ids is username, because new version FE will sent username"""
        profiles_selected = profiles_services.get_profile_by_usernames(
            selected_username=profile_ids
        )

        if len(profiles_selected) == 0:
            profiles_selected = profiles_services.get_profile_by_ids(
                selected_ids=profile_ids
            )

    profile_ids = [item.profile_id for item in profiles_selected]
    for profile_id in profile_ids:
        mission_schedule_instance = MissionSchedule(
            group_id, profile_id, new_mission.mission_id, schedule_json
        )
        db.session.add(mission_schedule_instance)

    tasks = data.get("tasks")
    for task in tasks:
        mission_task = MissionTask(new_mission.mission_id, task)
        if config:
            mission_task.config = config
        db.session.add(mission_task)
    db.session.flush()  # save tasks
    return new_mission


def update_mission(mission_id, data):
    """Update an existing mission."""
    mission = Mission.query.filter_by(mission_id=mission_id).first()
    if mission:
        for key, val in data.items():
            if hasattr(mission, key):
                mission.__setattr__(key, val)
        # Update other fields as necessary
        db.session.flush()
    return mission


def delete_mission(mission_id):
    """Delete a mission."""
    MissionSchedule.query.filter_by(mission_id=mission_id).delete()
    MissionTask.query.filter_by(mission_id=mission_id).delete()
    db.session.flush()
    # remove mission
    Mission.query.filter_by(mission_id=mission_id).delete()
    db.session.flush()
    return True
