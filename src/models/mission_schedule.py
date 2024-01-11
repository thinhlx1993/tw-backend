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
    'robot_id': UUID for the robot owning the mission(UUID) Foreign Key
    'mission_id': UUID for the mission(UUID) Foreign Key
    'schedule_json': JSON for the mission(JSONB)
    'timezone': Timezone for schedule(TEXT)
    'last_updated_at': Time for last updated(Timestamp)
    """

    __tablename__ = "mission_schedule"

    # Query class to handle soft deletion
    query_class = QueryWithSoftDelete

    schedule_id = db.Column(
        UUID(as_uuid=True), server_default=text("uuid_generate_v4()"),
        primary_key=True,
        comment='Unique identifier for schedule(Primary Key)')
    robot_id = db.Column(
        UUID(as_uuid=True), ForeignKey('robot.robot_id'),
        comment='Unique identifier for robot '
                'owning the schedule(Foreign Key)',
        nullable=False)
    mission_id = db.Column(
        UUID(as_uuid=True), ForeignKey('mission.mission_id'),
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
    mission_instances = relationship('MissionInstance')
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
    def __init__(self, robot_id, mission_id, schedule_json, timezone):
        self.robot_id = robot_id
        self.mission_id = mission_id
        self.schedule_json = schedule_json
        self.timezone = timezone

    def repr_name(self):
        """Custom representation of the model."""
        return {
            "schedule_id": str(self.schedule_id),
            "robot_id": str(self.robot_id),
            "mission_id": str(self.mission_id),
            "schedule_json": self.schedule_json,
            "timezone": self.timezone,
            "last_updated_at": str(self.last_updated_at.isoformat()),
            "start_timestamp": str(self.start_timestamp.isoformat()) if self.start_timestamp else ""
        }

    def repr_schedule_with_mission(self):
        """Custom representation of the model with mission name."""
        return {
            "schedule_id": str(self.schedule_id),
            "robot_id": str(self.robot_id),
            "mission_id": str(self.mission_id),
            "schedule_json": self.schedule_json,
            "timezone": self.timezone,
            "last_updated_at": str(self.last_updated_at.isoformat()),
            "mission_name": str(self.mission.mission_name),
            "start_timestamp": str(self.start_timestamp.isoformat()) if self.start_timestamp else ""
        }
