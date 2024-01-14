from src import db
from sqlalchemy import text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship


class Task(db.Model):
    """
    Model for tasks table
    Attributes:
    'tasks_id': Unique identifier for the task(UUID) PK
    'tasks_name': Name of the task(VARCHAR(256))
    'tasks_json': JSON for the task(JSONB)
    """
    __tablename__ = "tasks"

    tasks_id = db.Column(db.String(128), server_default=text("uuid_generate_v4()"), primary_key=True)
    tasks_name = db.Column(db.String(256))
    tasks_json = db.Column(JSONB)

    # Relationships
    mission_tasks = relationship("MissionTask", back_populates="task")

    def __repr__(self):
        return f"<Task {self.tasks_id} {self.tasks_name}>"

    def repr_name(self):
        return {
            "tasks_id": self.tasks_id,
            "tasks_name": self.tasks_name,
            "tasks_json": self.tasks_json
        }
