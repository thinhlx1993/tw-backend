from flask_jwt_extended import get_jwt_claims
from flask_migrate import upgrade
from sentry_sdk import capture_exception
from contextlib import contextmanager
from src import app, db
from sqlalchemy import text
from sqlalchemy.orm import scoped_session, sessionmaker

# Assuming db is your SQLAlchemy instance
Session = sessionmaker(bind=db.get_engine(app, bind='readonly'))


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


@contextmanager
def get_readonly_session():
    # Execute the command within this session
    """Provide a transactional scope around a series of operations."""
    session = Session()
    user_claims = get_jwt_claims()
    teams_id = user_claims['teams_id']
    session.execute(text(f"SET search_path TO public, 'cs_{teams_id}'"))
    try:
        yield session
    except Exception:
        raise
    finally:
        session.close()
