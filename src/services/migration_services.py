from flask_migrate import upgrade
from sentry_sdk import capture_exception

from src import app, db


def upgrade_database():
    """
    Run flask migrate upgrade
    """
    db.session.commit()
    upgrade()


def set_search_path(teams_id):
    """
    Set search path for session
    """
    try:
        db.session.execute("SET search_path TO public, 'cs_" + str(teams_id) + "'")
    except Exception as e:
        capture_exception(e)
        raise
