from flask_jwt_extended import get_jwt_claims
from flask_migrate import upgrade
from sentry_sdk import capture_exception

from src import app, db
from sqlalchemy import text
from sqlalchemy.orm import scoped_session, sessionmaker


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


def get_readonly_session():
    # Create a session bound to the 'readonly' engine
    Session = sessionmaker(bind=db.get_engine(app, bind='readonly'))
    session = Session()

    # Execute the command within this session
    user_claims = get_jwt_claims()
    teams_id = user_claims['teams_id']
    session.execute(text(f"SET search_path TO public, 'cs_{teams_id}'"))
    return session
