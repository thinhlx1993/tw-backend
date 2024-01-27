from src import db
from sqlalchemy import text, ForeignKey, func
from sqlalchemy.orm import relationship


class Events(db.Model):
    """
    Model for mission groups
    """

    __tablename__ = "events"

    event_id = db.Column(
        db.String(128), server_default=text("uuid_generate_v4()"), primary_key=True
    )
    event_type = db.Column(db.String(128), nullable=True)
    profile_id = db.Column(
        db.String(128), ForeignKey("profiles.profile_id"), nullable=False
    )
    profile_id_interact = db.Column(
        db.String(128), ForeignKey("profiles.profile_id"), nullable=True
    )
    schedule_id = db.Column(
        db.String(128), ForeignKey("mission_schedule.schedule_id"), nullable=True
    )
    mission_id = db.Column(
        db.String(128), ForeignKey("mission.mission_id"), nullable=True
    )
    user_id = db.Column(db.String(128), nullable=True)
    created_at = db.Column(db.DateTime(), nullable=False, server_default=func.now())
    issue = db.Column(db.Text(), nullable=True)

    def repr_name(self):
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "receiver": self.receiver.repr_name(),
            "giver": self.giver.repr_name(),
            "schedule_id": self.schedule_id,
            "mission_id": self.mission_id,
            "user_id": self.user_id,
            "issue": self.issue,
            "created_at": self.created_at.strftime("%d-%m-%Y %H:%M"),
        }
