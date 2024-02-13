import os
import logging

import jwt
from flask import request
from functools import wraps
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims, get_jwt_identity
from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError
from pydantic import ValidationError
from jwt import ExpiredSignatureError
from src import db

_logger = logging.getLogger(__name__)

"""
Check for valid JWT and
user claims should have
authorized as true 
"""


def custom_jwt_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user = get_jwt_claims()
            if user["authorized"]:
                db.session.execute(
                    "SET search_path TO public, 'cs_" + str(user["teams_id"]) + "'"
                )
                return fn(*args, **kwargs)
            else:
                return {"message": "Not authorized"}, 401

        return decorator

    return wrapper


def super_admin_required():
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user = get_jwt_claims()
            user_identity = get_jwt_identity()
            if user_identity != "thinhle.ict":
                return {"message": "Not authorized"}, 403

            if user["authorized"]:
                db.session.execute(
                    "SET search_path TO public, 'cs_" + str(user["teams_id"]) + "'"
                )
                return fn(*args, **kwargs)
            else:
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
                    "SET search_path TO public, 'cs_" + str(user["teams_id"]) + "'"
                )
                return fn(*args, **kwargs)
            except:
                return {"message": "Not authorized"}, 401

        return decorator

    return wrapper


def requires_apikey(f):
    """Decorator function that require an API Key"""

    @wraps(f)
    def decorated(*args, **kwargs):
        """Decorator function that does the checking"""
        try:
            api_key = os.environ.get("API_KEY")
            if f"Bearer {api_key}" == request.headers.get("Authorization"):
                return f(*args, **kwargs)
        except ValidationError as ex:
            return {"message": "Validation error", "data": str(ex)}, 400
        except Exception as ex:
            _logger.exception(ex)

        return {"message": "Not authorized"}, 401

    return decorated
