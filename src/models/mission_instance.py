"""Model for /mission_instance"""

from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import ForeignKey, func, text

from src import db


class MissionInstance(db.Model):
    """
    Model for mission_instance table.
    Attributes:
    'mission_instance_id' : mission_instance_id uuid(UUID)
    'robot_id': robot_id uuid(UUID)
    'mission_id': mission_id uuid(UUID)
    'mission_json': JSON for mission dict(JSONB)
    'start_timestamp': schedule start_timestamp str(DateTime)
    'end_timestamp': schedule end_timestamp str(DateTime)
    'is_cancelled': boolean to check schedule status boolean(Boolean)
    'is_complete': boolean to check schedule status boolean(Boolean)
    'is_deleted': boolean to check schedule status boolean(Boolean)
    'last_updated_at': latest updated timestamp str(DateTime)
    'schedule_id' schedule_id uuid(UUID)
    'success_category': category of the schedule str(String)
    'required_intervention': boolean to check for
                            user interventions dict(JSONB)
    'issues_recorded': JSON for issues in schedule dict(JSONB)
    """

    __tablename__ = "mission_instance"

    mission_instance_id = db.Column(
        db.String(128), server_default=text("uuid_generate_v4()"),
        primary_key=True, comment='Unique identifier '
        'for mission_instance(Primary Key)')
    mission_json = db.Column(JSONB, comment='JSON for mission')
    issues_recorded = db.Column(JSONB, comment='Issues for the mission')
    start_timestamp = db.Column(
        db.DateTime, comment='Start time for the mission')
    end_timestamp = db.Column(db.DateTime, comment='End time for the mission')
    last_updated_at = db.Column(
        db.DateTime(), server_default=func.now(),
        comment='Timestamp indicating when this was last updated')
    is_cancelled = db.Column(
        db.Boolean, server_default='false',
        comment='Boolean to check for cancelled missions')
    is_deleted = db.Column(
        db.Boolean, server_default='false',
        comment='Boolean to check for deleted missions')
    is_complete = db.Column(
        db.Boolean, server_default='false',
        comment='Boolean to check status of the mission completion')
    is_scheduled = db.Column(
        db.Boolean, server_default='false',
        comment='Boolean to check scheduled mission instance')
    required_intervention = db.Column(
        db.Boolean, server_default='false',
        comment='Boolean to check for interventions')
    success_category = db.Column(
        db.String(15), server_default='',
        comment='String for categorising missions')
    analysis_complete = db.Column(
        db.Boolean, server_default='false',
        comment='Boolean to check for mission analysis status'
    )
    robot_id = db.Column(
        db.String(128), ForeignKey("robot.robot_id"),
        nullable=False, comment='Unique identifier '
        'for robot(Foreign Key)')
    mission_id = db.Column(
        db.String(128), ForeignKey("mission.mission_id"),
        nullable=True, comment='Unique identifier '
        'for mission(Foreign Key)')
    schedule_id = db.Column(
        db.String(128), ForeignKey("mission_schedule.schedule_id"),
        nullable=True, comment='Unique identifier '
        'for mission_schedule(Foreign Key)')
    loop_count = db.Column(
        db.Integer,
        nullable=True,
        comment='Looping count for mission in schedule'
    )
    task_last_updated_at = db.Column(
        db.DateTime(),
        nullable=True,
        comment='Timestamp indicating when the task was last updated'
    )

    # Constructor initialising table columns
    def __init__(
            self, robot_id, start_timestamp, mission_json, mission_id=None,
            issues_recorded=None, end_timestamp=None, schedule_id=None, 
            is_deleted=False, is_complete=False, required_intervention=False,
            success_category=None, is_cancelled=False, is_scheduled=False,
            analysis_complete=False, loop_count=None):
        self.robot_id = robot_id
        self.mission_id = mission_id
        self.schedule_id = schedule_id
        self.mission_json = mission_json
        self.issues_recorded = issues_recorded
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.is_cancelled = is_cancelled
        self.is_deleted = is_deleted
        self.is_scheduled = is_scheduled
        self.is_complete = is_complete
        self.success_category = success_category
        self.required_intervention = required_intervention
        self.analysis_complete = analysis_complete
        self.loop_count = loop_count

    def repr_name(self):
        """Dict representation of model"""
        return {
            "mission_instance_id": str(self.mission_instance_id),
            "robot_id": str(self.robot_id),
            "robot_name": self.robot.nick_name if self.robot else None,
            "mission_id": str(self.mission_id) if self.mission_id else None,
            "mission_name": self.mission.mission_name if self.mission else None,
            "schedule_id": str(self.schedule_id) if self.schedule_id else None,
            "issues_recorded": self.issues_recorded,
            "start_timestamp": str(self.start_timestamp),
            "end_timestamp": str(self.end_timestamp) 
                if self.end_timestamp else None,
            "is_deleted": self.is_deleted,
            "is_cancelled": self.is_cancelled,
            "is_scheduled": self.is_scheduled,
            "success_category": self.success_category,
            "last_updated_at": str(self.last_updated_at),
            "required_intervention": self.required_intervention,
            "is_complete": self.is_complete,
            "mission_json": self.mission_json,
            "analysis_complete": self.analysis_complete
        }
