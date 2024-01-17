from sqlalchemy import text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from src import db


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

    mission_id = db.Column(
        db.String(128),
        server_default=text("uuid_generate_v4()"),
        primary_key=True,
        comment="Unique identifier " "for mission(Primary Key)",
    )
    mission_name = db.Column(db.String(256), comment="Name of the mission")
    group_id = db.Column(db.String(128), ForeignKey("groups.group_id"), nullable=True)
    user_id = db.Column(db.String(128), nullable=False)
    mission_json = db.Column(JSONB, comment="JSON for mission")
    mission_schedule = relationship(
        "MissionSchedule", cascade="all,delete", backref="mission"
    )
    deleted_at = db.Column(
        db.DateTime(),
        nullable=True,
        comment="Timestamp indicating when the record was soft deleted",
    )
    mission_tasks = relationship("MissionTask", back_populates="mission")

    def repr_name(self):
        return {
            "mission_id": self.mission_id,
            "mission_name": self.mission_name,
            "user_id": self.user_id,
            "group_id": self.group_id,
            "mission_json": self.mission_json,
        }
