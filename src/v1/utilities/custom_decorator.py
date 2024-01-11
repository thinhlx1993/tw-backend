import logging
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims, get_jwt_identity
from jwt import ExpiredSignatureError
from src import db
from src.v1.models import User

"""
Check for valid JWT and
user claims should have
authorized as true 
"""


def custom_jwt_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user = get_jwt_claims()
                if user['authorized']:
                    db.session.execute(
                        "SET search_path TO public, 'cs_" +
                        str(user['organization_id']) + "'")
                    return fn(*args, **kwargs)
                else:
                    return {"message": "Not authorized"}, 401
            except ExpiredSignatureError:
                   return {"message":"Authorization token expired"},401
            except Exception as ex:
                return {"message": "Not authorized"}, 401
        return decorator
    return wrapper


def any_jwt_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                verify_jwt_in_request()
                user = get_jwt_claims()
                db.session.execute(
                    "SET search_path TO public, 'cs_" +
                    str(user['organization_id']) + "'")
                return fn(*args, **kwargs)
            except:
                return {"message": "Not authorized"}, 401
        return decorator
    return wrapper


# Authentication decorator
def admin_required(fn):
    """
    A decorator to protect a Flask endpoint.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            user_id = get_jwt_identity()
            user = User.query.filter(User.user_id == user_id).first()
            user_groups = [group.name for group in user.groups]
            if 'administrator' in user_groups:
                return fn(*args, **kwargs)
        except Exception as ex:
            logging.exception(ex)

        return {"message": "You don't have permissions to do this action"}, 403

    return wrapper
