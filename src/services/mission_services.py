from src import db
from src.models import Mission


def get_all_missions():
    """Retrieve all missions."""
    return Mission.query.all()


def create_mission(data):
    """Create a new mission."""
    new_mission = Mission()
    for key, val in data.items():
        if hasattr(new_mission, key):
            new_mission.__setattr__(key, val)
    db.session.add(new_mission)
    db.session.commit()
    return new_mission


def update_mission(mission_id, data):
    """Update an existing mission."""
    mission = Mission.query.filter_by(mission_id=mission_id).first()
    if mission:
        for key, val in data.items():
            if hasattr(mission, key):
                mission.__setattr__(key, val)
        # Update other fields as necessary
        db.session.flush()
    return mission


def delete_mission(mission_id):
    """Delete a mission."""
    mission = Mission.query.filter_by(mission_id=mission_id).first()
    if mission:
        db.session.delete(mission)
        db.session.flush()
        return True
    return False
