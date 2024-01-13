"""Services for teams."""
import datetime
import logging
import math
import re

from sentry_sdk import capture_exception
from sqlalchemy import func, text, and_
from sqlalchemy.exc import MultipleResultsFound

from src import db
from src.models.profiles import Profiles
from src.models.groups import Groups
from src.models.teams import Teams
from src.models.user_teams_mapping import UserTeamsMapping
from src.services import user_services, migration_services

# Create module log
_logger = logging.getLogger(__name__)


def create_profile(data):
    new_profile = Profiles()
    for key, val in data.items():
        if hasattr(new_profile, key):
            new_profile.__setattr__(key, str(val))

    db.session.add(new_profile)
    db.session.flush()
    return new_profile


def get_profile_by_id(profile_id):
    return Profiles.query.get(profile_id)


def get_profile_by_username(username):
    return Profiles.query.filter_by(username=username).first()


def get_all_profiles(page=0, per_page=20, sort_by="created_at", sort_order="asc", search="", group_id=""):
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
            query = query.filter(Profiles.username.ilike(f'%{search}%'))
        if group_id and group_id != "All":
            query = query.filter(Profiles.group_id == group_id)
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
            "max_pages": math.ceil(count/per_page)
        }
    except Exception as err:
        _logger.exception(err)
        db.session.rollback()
        capture_exception(err)
        raise err


def update_profile(profile_id, data):
    profile = Profiles.query.get(profile_id)
    if profile:
        for key, value in data.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        profile.modified_at = datetime.datetime.now()
        db.session.flush()
        return profile
    return None


def delete_profile(profile_id):
    profile = Profiles.query.get(profile_id)
    if profile:
        db.session.delete(profile)
        db.session.commit()
        return True
    return False
