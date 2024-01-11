import json
import logging
import os
import traceback

import sentry_sdk
from werkzeug.exceptions import NotFound as InvalidURLException
from flask import jsonify, request, Response, send_from_directory, send_file

from src import app, db, jwt
from src.v1.models import AuthTokenBlacklist
from src.v1.controllers import auth, users, file_upload, upload
from src.version_handler import version_1_web, api_version_1_web


api_version_1_web.add_namespace(auth.auth_ns)
api_version_1_web.add_namespace(users.users_ns)
api_version_1_web.add_namespace(file_upload.files_ns)
api_version_1_web.add_namespace(upload.upload_files_ns)
app.register_blueprint(version_1_web, url_prefix='/user/v1')

_logger = logging.getLogger(__name__)


sentry_sdk.init(
    dsn="https://bf651016a6029f4f008b902578b10f3f@o1068161.ingest.sentry.io/4506552476499968",
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100%
    # of sampled transactions.
    # We recommend adjusting this value in production
)


@app.before_request
def log_request_info():
    _logger.debug(
        {
            "request": {
                "remote_addr": request.remote_addr,
                "method": request.method,
                "scheme": request.scheme,
                "full_path": request.full_path,
                "headers": request.headers,
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
    else:
        db.session.rollback()
    return response


@app.route("/ping")
def ping():
    """
    Basic healthcheck route
    """
    return jsonify({"Status": "Alive"}), 200


@jwt.token_in_blacklist_loader
def check_if_token_revoked(jwt_payload: dict) -> bool:
    jti = jwt_payload["jti"]
    token = (
        db.session.query(AuthTokenBlacklist.token_id)
        .filter(AuthTokenBlacklist.jti == jti, AuthTokenBlacklist.revoked == True)
        .scalar()
    )

    return token is not None


# Middleware to add all claims to JWT
@jwt.user_claims_loader
def add_claims_to_access_token(payload):
    """
    Middleware that adds claims to JWT
    """
    if payload["type"] == "access":
        return {
            "user_id": payload["user_id"],
            "authorized": payload["authorized"],
            "refresh_jti": payload["refresh_jti"],
        }
    elif payload["type"] == "refresh":
        return {"user_id": payload["user_id"], "refresh_jti": payload["refresh_jti"]}


@jwt.user_identity_loader
def user_identity_lookup(payload):
    return payload["user_id"]


@app.route('/uploads/<name>')
def download_file(name):
    return send_from_directory("../" + app.config["UPLOAD_FOLDER"], name)
    # return send_file(f"uploads/{name}")


app.add_url_rule(
    "/uploads/<name>", endpoint="download_file", build_only=True
)
