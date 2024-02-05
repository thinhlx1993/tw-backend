from src import db
from sqlalchemy import text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship


class MissionTask(db.Model):
    """
    Association table for the many-to-many relationship between missions and tasks
    """
    __tablename__ = 'mission_tasks'

    mission_id = db.Column(db.String(128), db.ForeignKey('mission.mission_id'), primary_key=True)
    tasks_id = db.Column(db.String(128), db.ForeignKey('tasks.tasks_id'), primary_key=True)
    config = db.Column(db.JSON(), nullable=True)

    # Relationships
    mission = relationship("Mission", back_populates="mission_tasks")
    task = relationship("Task", back_populates="mission_tasks")

    def __init__(self, mission_id, tasks_id):
        self.tasks_id = tasks_id
        self.mission_id = mission_id

    def __repr__(self):
        return f"<MissionTask mission_id={self.mission_id} tasks_id={self.tasks_id}>"

    def repr_name(self):
        return {
            "mission_id": self.mission_id,
            "tasks_id": self.tasks_id,
            "tasks": self.task.repr_name(),
            "config": self.config
        }
