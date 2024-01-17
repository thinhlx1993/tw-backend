"""Model for MissionSchedule table."""
import datetime

from sqlalchemy import ForeignKey, func, text
from sqlalchemy.dialects.postgresql import JSONB, TEXT, UUID
from sqlalchemy.orm import relationship

from src import db
from src.query.query_with_soft_delete import QueryWithSoftDelete


class MissionSchedule(db.Model):

    """Model for mission_schedule table.

    Attributes:
    'schedule_id': UUID for the schedule(UUID) Primary Key
    'group_id': UUID for the groups owning the mission(UUID) Foreign Key
    'mission_id': UUID for the mission(UUID) Foreign Key
    'schedule_json': JSON for the mission(JSONB)
    'timezone': Timezone for schedule(TEXT)
    'last_updated_at': Time for last updated(Timestamp)
    """

    __tablename__ = "mission_schedule"

    schedule_id = db.Column(
        db.String(128), server_default=text("uuid_generate_v4()"),
        primary_key=True,
        comment='Unique identifier for schedule(Primary Key)')
    group_id = db.Column(
        db.String(128), ForeignKey('groups.group_id'),
        nullable=False)
    profile_id = db.Column(
        db.String(128),
        ForeignKey('profiles.profile_id'),
        nullable=True)
    mission_id = db.Column(
        db.String(128), ForeignKey('mission.mission_id'),
        comment='Unique identifier for mission(Foreign Key)',
        nullable=False)
    schedule_json = db.Column(JSONB, comment='JSON for schedule')
    timezone = db.Column(TEXT, comment='Timezone for schedule')
    last_updated_at = db.Column(
        db.DateTime(), server_default=func.now(),
        comment='Timestamp indicating when this was last updated')
    start_timestamp = db.Column(
        db.DateTime(),
        server_default=func.now(),  # give some value for existing rwos, it will help us in querying the db
        comment='Schedule will be available for fetch or search after this date',
        nullable=False)
    end_timestamp = db.Column(
        db.DateTime(),
        nullable=True,
        comment='Timestamp indicating when the scheduled is supposed to end'
    )
    deleted_at = db.Column(
        db.DateTime(),
        nullable=True,
        comment='Timestamp indicating when the record was soft deleted'
    )

    # Constructor initializing values
    def __init__(self, group_id, profile_id, mission_id, schedule_json):
        self.group_id = group_id
        self.profile_id = profile_id
        self.mission_id = mission_id
        self.schedule_json = schedule_json

    def repr_name(self):
        """Custom representation of the model."""
        return {
            "schedule_id": self.schedule_id,
            "group_id": self.group_id,
            "profile_id": self.profile_id,
            "mission_id": self.mission_id,
            "schedule_json": self.schedule_json,
            "start_timestamp": self.start_timestamp.strftime("%d-%m-%Y %H:%M") if self.start_timestamp else None
        }

    def repr_schedule_with_mission(self):
        """Custom representation of the model with mission name."""
        return {
            "schedule_id": self.schedule_id,
            "group_id": self.group_id,
            "profile_id": self.profile_id,
            "mission_id": self.mission_id,
            "schedule_json": self.schedule_json,
            "start_timestamp": self.start_timestamp.strftime("%d-%m-%Y %H:%M") if self.start_timestamp else None
        }
