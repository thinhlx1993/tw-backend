import json
import traceback

from werkzeug.exceptions import NotFound as InvalidURLException
from flask import jsonify, request
from sentry_sdk import capture_exception
from src import app
from src import db
from src import jwt
from src import v1
from src.version_handler import version_1_web
from src.log_config import _logger

app.register_blueprint(version_1_web, url_prefix="/api/v1")


@app.before_request
def log_request_info():
    _logger.info(
        {
            "request": {
                "remote_addr": request.remote_addr,
                "method": request.method,
                "scheme": request.scheme,
                "full_path": request.full_path,
                "data": request.get_data(),
            }
        }
    )


@app.errorhandler(InvalidURLException)
def not_found(e):
    data = {"message": "Not Found"}
    response = app.response_class(
        response=json.dumps(data), status=404, mimetype="application/json"
    )
    return response


@app.errorhandler(Exception)
def exceptions(e):
    tb = traceback.format_exc()
    _logger.error(
        "%s %s %s %s 5xx INTERNAL SERVER ERROR\n%s",
        request.remote_addr,
        request.method,
        request.scheme,
        request.full_path,
        tb,
    )
    capture_exception(e)
    data = {"message": str(e)}
    response = app.response_class(
        response=json.dumps(data), status=500, mimetype="application/json"
    )
    return response


@app.after_request
def after_request(response):
    _logger.debug(
        "%s %s %s %s %s",
        request.remote_addr,
        request.method,
        request.scheme,
        request.full_path,
        response.status_code,
    )
    return response


@app.after_request
def after_request_func(response):
    if response.status_code in [200, 201]:
        db.session.commit()
    return response


@app.route("/ping")
def ping():
    """
    Basic healthcheck route
    """
    return jsonify({"Status": "Alive"}), 200


@jwt.user_claims_loader
def add_claims_to_access_token(payload):
    """
    Middleware that adds claims to JWT
    """
    if payload["type"] == "access":
        return {
            "user_id": payload["user_id"],
            "device_id": payload["device_id"],
            "user": payload["user"],
            "role": payload["role"],
            "permissions": payload["permissions"],
            "default_page": payload["default_page"],
            "profile_name": payload["profile_name"],
            "teams_id": payload["teams_id"],
            "teams_code": payload["teams_code"],
            "authorized": payload["authorized"],
            "refresh_jti": payload["refresh_jti"],
        }
    elif payload["type"] == "refresh":
        return {
            "teams_id": payload["teams_id"],
            "teams_code": payload["teams_code"],
            "device_id": payload["device_id"]
        }


@jwt.user_identity_loader
def user_identity_lookup(payload):
    return payload["user"]
