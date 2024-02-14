"""Services for groups."""

import logging
from src import db, app
from src.models.groups import Groups

# Create module log
_logger = logging.getLogger(__name__)


def create_group(data):
    new_group = Groups()
    for key, val in data.items():
        if hasattr(new_group, key):
            new_group.__setattr__(key, val)
    db.session.add(new_group)
    db.session.flush()
    return new_group


def get_group_by_id(group_id):
    return (
        Groups.query.filter_by(group_id=group_id)
        .execution_options(bind=db.get_engine(app, bind="readonly"))
        .first()
    )


def get_all_groups():
    groups = Groups.query.execution_options(
        bind=db.get_engine(app, bind="readonly")
    ).all()
    groups = [group.repr_name() for group in groups]
    return groups


def update_group(group_id, data):
    group = Groups.query.filter_by(group_id=group_id).first()
    if group:
        for key, val in data.items():
            if hasattr(group, key):
                group.__setattr__(key, val)
        db.session.flush()
        return group
    return None  # Or handle the case where the group is not found


def delete_group(group_id):
    group = Groups.query.filter_by(group_id=group_id).first()
    if group:
        db.session.delete(group)
        db.session.flush()
        return True
    return False  # Or handle the case where the group is not found
