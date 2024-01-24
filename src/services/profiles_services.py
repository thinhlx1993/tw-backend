"""Services for teams."""
import datetime
import logging
import math

from sentry_sdk import capture_exception
from sqlalchemy import text, or_

from src import db
from src.models.profiles import Profiles
from src.models.teams import Teams
from src.services import hma_services

# Create module log
_logger = logging.getLogger(__name__)


def create_profile(data, device_id, user_id):
    username = data.get("username", "").strip()
    new_profile = Profiles.query.filter_by(username=username).first()
    if not new_profile:
        new_profile = Profiles()
        for key, val in data.items():
            if hasattr(new_profile, key):
                if isinstance(val, str):
                    val = val.strip()
                if val:
                    new_profile.__setattr__(key, val)

    hma_profile_id = hma_services.create_hma_profile(username, device_id, user_id)
    # if not hma_profile_id:
    #     raise Exception("Can not create HMA profiles, check your settings or HMA account")
    new_profile.hma_profile_id = hma_profile_id
    db.session.add(new_profile)
    db.session.flush()
    return new_profile


def get_profile_by_id(profile_id):
    return Profiles.query.get(profile_id)


def get_profile_by_username(username):
    return Profiles.query.filter_by(username=username).first()


def get_total_profiles():
    return Profiles.query.filter_by().count()


def get_all_profiles(
    page=0, per_page=20, sort_by="created_at", sort_order="desc", search="", group_id=""
):
    column = getattr(Teams, sort_by, None)
    if not column:
        return False, {"Message": "Invalid sort_by Key provided"}
    sorting_order = sort_by + " " + sort_order
    try:
        query = Profiles.query
        # Apply sorting
        if sorting_order:
            query = query.order_by(text(sorting_order))
        if search:
            query = query.filter(
                or_(
                    Profiles.username.ilike(f"%{search}%"),
                    Profiles.user_access.ilike(f"%{search}%"),
                )
            )
        # Apply pagination
        count = query.count()

        if per_page:
            query = query.limit(per_page)
        if page:
            query = query.offset(per_page * (page - 1))
        profiles = query.all()
        # Formatting the result
        formatted_result = [profile.repr_name() for profile in profiles]
        return {
            "profiles": formatted_result,
            "result_count": count,
            "max_pages": math.ceil(count / per_page),
        }
    except Exception as err:
        _logger.exception(err)
        db.session.rollback()
        capture_exception(err)
        raise err


def get_user_profiles(user_id):
    # username = user_detail.user_id
    profiles = Profiles.query.filter_by(owner=user_id).all()
    formatted_result = [profile.repr_name() for profile in profiles]
    return {"profiles": formatted_result}


def update_profile(profile_id, data):
    profile = Profiles.query.get(profile_id)
    if profile:
        for key, value in data.items():
            if hasattr(profile, key):
                if isinstance(value, str):
                    value = value.strip()
                setattr(profile, key, value)
        profile.modified_at = datetime.datetime.now()
        db.session.flush()
        return profile
    return None


def delete_profile(profile_id, user_id, device_id):
    hma_services.delete_browser_profile(profile_id, user_id, device_id)
    profile = Profiles.query.get(profile_id)
    if profile:
        db.session.delete(profile)
        db.session.flush()
        return True
    return False
