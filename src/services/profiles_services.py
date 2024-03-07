"""Services for teams."""

import datetime
import logging
import math

from sqlalchemy import or_, func, cast, Text

from src import db
from src.models.profiles import Profiles
from src.services import hma_services, migration_services

# Create module log
_logger = logging.getLogger(__name__)


def create_profile(data, device_id, user_id, hma_token, browser_version, teams_id):
    migration_services.set_search_path(teams_id)
    username = data.get("username", "").strip()
    if not username:
        return None
    profile = Profiles.query.filter(Profiles.username == username).first()

    if profile and profile.owner != user_id and profile.is_disable == False:
        return None

    if not profile:
        profile = Profiles()

    profile.created_at = datetime.datetime.utcnow()
    profile.is_disable = False
    for key, val in data.items():
        if hasattr(profile, key):
            if key == "click_count":
                continue
            if isinstance(val, str):
                val = val.strip()
            if val:
                profile.__setattr__(key, val)

    hma_profile_id = hma_services.create_hma_profile(
        username, device_id, user_id, hma_token, browser_version
    )
    if not hma_profile_id:
        return False
    profile.hma_profile_id = hma_profile_id
    profile.cookies = ""
    db.session.add(profile)
    db.session.commit()
    print(f"Add ok {username}")
    return profile


def get_profile_by_id(profile_id):
    return Profiles.query.get(profile_id)


def get_all_profiles(
    page=0,
    per_page=20,
    sort_by="created_at",
    sort_order="desc",
    search="",
    user_id="",
    filter_by_type="all",
):
    # column = getattr(Teams, sort_by, None)
    # if not column:
    #     return False, {"Message": "Invalid sort_by Key provided"}
    # sorting_order = sort_by + " " + sort_order
    query = db.session.query(Profiles)
    # Apply sorting
    # if sorting_order:
    query = query.filter(Profiles.is_disable == False)
    query = query.order_by(db.text("created_at asc"))
    if search:
        query = query.filter(
            or_(
                Profiles.username.ilike(f"%{search}%"),
                Profiles.user_access.ilike(f"%{search}%"),
                Profiles.status.ilike(f"%{search}%"),
            )
        )
    if user_id:
        query = query.filter(Profiles.owner == user_id)

    if filter_by_type == "main_account":
        query = query.filter(Profiles.main_profile == True)
    elif filter_by_type == "monetizable":
        query = query.filter(
            func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
                ["OK"]
            )
        )
    elif filter_by_type == "error":
        query = query.filter(
            func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
                ["ERROR"]
            )
        )
    elif filter_by_type == "AdsEligible":
        query = query.filter(
            func.json_extract_path_text(Profiles.profile_data, "account_status").in_(
                ["AdsEligible"]
            )
        )
    elif filter_by_type == "suspended":
        query = query.filter(cast(Profiles.profile_data["suspended"], Text) == "true")
    elif filter_by_type == "verified":
        query = query.filter(cast(Profiles.profile_data["verify"], Text) == "true")
    elif filter_by_type == "not_verified":
        query = query.filter(cast(Profiles.profile_data["verify"], Text) == "false")
    elif filter_by_type == "unknown":
        query = query.filter(Profiles.profile_data.is_(None))
    elif filter_by_type == "clone_account":
        query = query.filter(Profiles.main_profile == False)

    # Apply pagination
    count = query.count()

    if per_page:
        query = query.limit(per_page)
    if page:
        query = query.offset(per_page * (page - 1))
    profiles = query.all()
    # Formatting the result
    formatted_result = [profile.repr_data() for profile in profiles]
    return {
        "profiles": formatted_result,
        "result_count": count,
        "max_pages": math.ceil(count / per_page),
    }


def get_user_profiles(user_id):
    # username = user_detail.user_id
    profiles = Profiles.query.filter_by(owner=user_id, is_disable=False).all()
    formatted_result = [profile.repr_name() for profile in profiles]
    return {"profiles": formatted_result}


def update_profile(profile_id, data):
    profile = Profiles.query.get(profile_id)
    if profile:
        for key, value in data.items():
            if key == "username":
                continue

            if hasattr(profile, key):
                if isinstance(value, str):
                    value = value.strip()
                setattr(profile, key, value)
        profile.modified_at = datetime.datetime.utcnow()
        db.session.flush()
        return profile
    return None


def delete_profile(profile_id, user_id, device_id):
    profile = Profiles.query.get(profile_id)
    profile.is_disable = True
    # Events.query.filter_by(profile_id=profile_id).delete()
    # Events.query.filter_by(profile_id_interact=profile_id).delete()
    # Posts.query.filter_by(profile_id=profile_id).delete()
    # db.session.delete(profile)
    db.session.commit()
    return True


def get_profile_by_usernames(selected_username: list):
    profiles = (
        db.session.query(Profiles.profile_id)
        .filter(Profiles.username.in_(selected_username), Profiles.is_disable == False)
        .all()
    )
    return profiles


def get_profile_by_ids(selected_ids: list):
    profiles = (
        db.session.query(Profiles.profile_id)
        .filter(Profiles.profile_id.in_(selected_ids), Profiles.is_disable == False)
        .all()
    )
    return profiles


def get_profile_by_user(user_id: str):
    profiles = (
        db.session.query(Profiles.profile_id)
        .filter(Profiles.owner == user_id, Profiles.is_disable == False)
        .all()
    )
    return profiles
