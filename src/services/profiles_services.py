"""Services for teams."""

import logging
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
            new_profile.__setattr__(key, val)

    db.session.add(new_profile)
    db.session.flush()
    return new_profile


def get_profile_by_id(profile_id):
    return Profiles.query.get(profile_id)


def get_profile_by_username(username):
    return Profiles.query.filter_by(username=username).first()


def get_all_profiles():
    profiles = Profiles.query.all()
    profiles = [profile.repr_name() for profile in profiles]
    return profiles


def update_profile(profile_id, **kwargs):
    profile = Profiles.query.get(profile_id)
    if profile:
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
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
