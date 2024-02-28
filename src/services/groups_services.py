"""Services for groups."""

import logging

from sqlalchemy import func

from src import db, app
from src.models.groups import Groups
from src.views.groups import GroupViews

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
    return Groups.query.filter_by(group_id=group_id).first()


def get_all_groups():
    groups = db.session.query(Groups).order_by(db.text("group_name asc")).all()
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


def get_group_below_threshold():
    group = GroupViews.query.filter(
        GroupViews.group_id == "4f712930-bb96-4aab-9a98-80794612e193",
        GroupViews.total_clicks_giver > GroupViews.total_clicks_receiver,
    ).first()
    # group = (
    #     Groups.query.filter(
    #         Groups.group_id == "4f712930-bb96-4aab-9a98-80794612e193",
    #         Groups.click_count > Groups.receiver_count,
    #     )
    #     .order_by(func.random())
    #     .first()
    # )

    if not group:
        group = GroupViews.query.filter(
            GroupViews.total_clicks_giver > GroupViews.total_clicks_receiver,
        ).first()

    return group
