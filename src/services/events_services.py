import datetime
import math

from sqlalchemy import text, or_, func

from src import db
from src.models import Profiles, Events
from sqlalchemy.orm import aliased

from src.services.mission_schedule_services import should_start_job
from src.v1.dto.event_type import EventType
from src.log_config import _logger


def get_event_by_id(event_id):
    """Retrieve an event by its ID."""
    event_record = Events.query.filter_by(event_id=event_id).first()
    return event_record


def get_all_events(
    page=0,
    per_page=20,
    sort_by="created_at",
    sort_order="desc",
    search="",
    profile_id="",
    event_type="",
    user_id="",
    receiver_username="",
    giver_username="",
):
    # Aliases for Profiles table for giver and receiver
    giver_profile = aliased(Profiles)
    receiver_profile = aliased(Profiles)
    today_date = datetime.datetime.utcnow().date()
    # Specify the column from Events for sorting
    if sort_by == "created_at":
        column = Events.created_at
    else:
        column = getattr(Events, sort_by, None)

    if not column:
        return False, {"Message": "Invalid sort_by Key provided"}

    sorting_order = f"{column} {sort_order}"
    query = (
        db.session.query(Events)
        .join(giver_profile, Events.profile_id_interact == giver_profile.profile_id)
        .join(receiver_profile, Events.profile_id == receiver_profile.profile_id)
    )

    query = query.filter(db.func.date(Events.created_at) == today_date)
    query = query.filter(Events.issue == 'OK')
    # Apply sorting
    if sorting_order:
        query = query.order_by(text(sorting_order))

    # Apply filters
    if event_type:
        query = query.filter(func.lower(Events.event_type) == func.lower(event_type))
    if search:
        search = search.strip().lower()
        query = query.filter(
            or_(
                func.lower(Events.issue).ilike(f"%{search}%"),
                func.lower(Events.event_type).ilike(f"%{search}%"),
            )
        )
    if profile_id:
        query = query.filter(Events.profile_id == profile_id)
    if user_id:
        query = query.filter(Events.user_id == user_id)
    if receiver_username:
        receiver_username = receiver_username.strip().lower()
        query = query.filter(
            func.lower(receiver_profile.username) == func.lower(receiver_username)
        )
    if giver_username:
        giver_username = giver_username.strip().lower()
        query = query.filter(
            func.lower(giver_profile.username) == func.lower(giver_username)
        )

    # Apply pagination
    count = query.count()
    if per_page:
        query = query.limit(per_page)
    if page:
        query = query.offset(per_page * (page - 1))

    events = query.all()

    # Formatting the result
    formatted_result = [event.repr_name() for event in events]

    return {
        "data": formatted_result,
        "result_count": count,
        "max_pages": math.ceil(count / per_page),
    }


def create_or_update_event(event_id, event_data):
    """Create or update an event."""
    event_record = Events.query.filter_by(event_id=event_id).first()

    if event_record:
        # Update existing record with new data
        for key, value in event_data.items():
            setattr(event_record, key, value)
    else:
        # Create a new record
        event_record = Events()
        event_record.created_at = datetime.datetime.utcnow()
        # "event_type": fields.String(required=True, example="event_type"),
        # "profile_id": fields.String(required=False, example="profile_id"),
        # "profile_id_interact": fields.String(required=True, example="profile_id"),
        event_type = event_data.get('event_type')
        profile_id_receiver = event_data.get('profile_id')
        profile_id_giver = event_data.get('profile_id_interact')
        issue = event_type.get('issue')

        if issue == "OK":
            update_count(profile_id_receiver, event_type)
            update_count(profile_id_giver, event_type)

        for key, val in event_data.items():
            if hasattr(event_record, key):
                event_record.__setattr__(key, val)

        db.session.add(event_record)

    db.session.flush()
    return event_record


def update_count(profile_id, event_type):
    profile_receiver = Profiles.query.filter(Profiles.profile_id == profile_id).first()
    today = datetime.datetime.utcnow().date()
    _logger.info(f'Today is {today}  and profile date {profile_receiver.modified_at.date()}')
    if profile_receiver.modified_at.date() != today:
        profile_receiver.click_count = 0
        profile_receiver.comment_count = 0
        profile_receiver.like_count = 0

    click_count = profile_receiver.click_count
    comment_count = profile_receiver.comment_count
    like_count = profile_receiver.like_count

    # update event count for profile
    if event_type == EventType.CLICK_ADS.value:
        if not click_count:
            click_count = 0
        click_count += 1
        profile_receiver.click_count = click_count
    elif event_type == EventType.COMMENT.value:
        if not comment_count:
            comment_count = 0
        comment_count += 1
        profile_receiver.comment_count = comment_count
    elif event_type == EventType.LIKE.value:
        if not like_count:
            like_count = 0
        like_count += 1
        profile_receiver.like_count = like_count
    profile_receiver.modified_at = datetime.datetime.utcnow()
    _logger.info('Update event count ok')
    db.session.flush()


def delete_event(event_id):
    """Delete an event by its ID."""
    event_record = Events.query.filter_by(event_id=event_id).first()
    if event_record:
        db.session.delete(event_record)
        db.session.flush()
        return True
    return False
