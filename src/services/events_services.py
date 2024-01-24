import math

from sqlalchemy import text, or_

from src import db
from src.models.events import Events  # Importing the Events model


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
):
    column = getattr(Events, sort_by, None)
    if not column:
        return False, {"Message": "Invalid sort_by Key provided"}
    sorting_order = sort_by + " " + sort_order
    query = Events.query
    # Apply sorting
    if sorting_order:
        query = query.order_by(text(sorting_order))
    if event_type:
        query.filter(Events.event_type == event_type)
    if search:
        query = query.filter(
            or_(
                Events.issue.ilike(f"%{search}%"),
                Events.event_type.ilike(f"%{search}%"),
            )
        )
    if profile_id:
        query.filter(Events.profile_id == profile_id)
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
        for key, val in event_data.items():
            if hasattr(event_record, key):
                event_record.__setattr__(key, val)
        db.session.add(event_record)

    db.session.flush()
    return event_record


def delete_event(event_id):
    """Delete an event by its ID."""
    event_record = Events.query.filter_by(event_id=event_id).first()
    if event_record:
        db.session.delete(event_record)
        db.session.flush()
        return True
    return False
