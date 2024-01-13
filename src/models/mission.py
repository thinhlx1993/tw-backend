from sqlalchemy import text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship


from src import db
from src.query.query_with_soft_delete import QueryWithSoftDelete

class Mission(db.Model):
    """
    Model for mission table
    Attributes:
    'mission_id': Unique identifier for the mission(UUID) PK
    'mission_name': Name of the mission(VARCHAR(256))
    'robot_id': Unique identifier for the robot owning the mission(UUID) FK
    'mission_json': JSON for the mission(JSONB)
    """
    __tablename__ = "mission"

    # Query class to handle soft deletion
    query_class = QueryWithSoftDelete

    mission_id = db.Column(db.String(128), server_default=text(
        "uuid_generate_v4()"), primary_key=True, comment='Unique identifier '
        'for mission(Primary Key)')
    mission_name = db.Column(db.String(256), comment='Name of the mission')
    robot_id = db.Column(db.String(128), ForeignKey(
        'robot.robot_id'), comment='Unique identifier for robot '
        'owning the mission(Foreign Key)', nullable=False)
    mission_json = db.Column(JSONB, comment='JSON for mission')
    mission_schedule = relationship('MissionSchedule', cascade='all,delete',
        backref='mission')
    mission_instances = relationship(
        'MissionInstance', cascade='all,delete', backref="mission")
    deleted_at = db.Column(
        db.DateTime(),
        nullable=True,
        comment='Timestamp indicating when the record was soft deleted'
    )

    # Constructor initializing values
    def __init__(self, mission_id, mission_name, robot_id, mission_json):
        self.mission_id = mission_id
        self.mission_name = mission_name
        self.robot_id = robot_id
        self.mission_json = mission_json

    def repr_name(self):
        return {
            "mission_id": str(self.mission_id),
            "mission_name": str(self.mission_name),
            "robot_id": str(self.robot_id),
            "mission_json": self.mission_json
        }
    