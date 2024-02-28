from src import db
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func, text, ForeignKey
from sqlalchemy.dialects.postgresql import BYTEA


class GroupViews(db.Model):
    __tablename__ = "group_summary_view"
    group_id = db.Column(
        db.String(128), server_default=text("uuid_generate_v4()"), primary_key=True
    )
    group_name = db.Column(db.String(128))
    total_profiles = db.Column(db.Integer)
    profile_giver = db.Column(db.Integer)
    profile_receiver = db.Column(db.Integer)
    total_clicks_giver = db.Column(db.Integer)
    total_clicks_receiver = db.Column(db.Integer)
