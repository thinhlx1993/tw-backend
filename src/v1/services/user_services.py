import logging
import datetime
import json
import uuid
import time
import requests
import re
import os
from enum import Enum
from concurrent.futures import ThreadPoolExecutor

import bcrypt
import pyotp
import pyqrcode
from cryptography.fernet import Fernet
from flask_jwt_extended import create_access_token
from flask_jwt_extended import create_refresh_token, get_jti
from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer,
    BadData,
)

from src import db, app
from src.config import Config
from src.custom_exceptions import InvalidJWTToken
from src.v1.models import AuthTokenBlacklist, UserPasswordResetToken
from src.v1.models.user import User, UserRole
from src.v1.validator.paginator import PaginatorModel

# Create module log
_logger = logging.getLogger(__name__)


def validate_password(user_password, input_password):
    """
    Validates password against hash stored in database

    :param str user_password: Username to fetch details of user
    :param str input_password: User input password that needs to be validated

    :return: True if password is valid, False if password is invalid.
    """
    # Check input password against hashed password in DB
    return bcrypt.checkpw(input_password.encode("utf-8"), user_password.encode("utf-8"))


def create_user(email):
    """
    Creates a user
    :param str email: Email ID for the user
    :return User user: User object created from the params
    """
    user = User(email=email)
    db.session.add(user)
    db.session.flush()
    return user


def blacklist_token(jti, user_id):
    """
    Blacklist the token
    :param str jit: jit to be blacklisted
    """
    blocker = AuthTokenBlacklist.query.filter_by(jti=jti).first()
    if blocker:
        blocker.revoked = True
        db.session.flush()
    else:
        auth_instance = AuthTokenBlacklist(
            jti=jti,
            created_at=datetime.datetime.now(),
            user_id=user_id,
            revoked=True,
        )
        db.session.add(auth_instance)
        db.session.commit()


def reset_password(username, password):
    """
    Resets password for the username in param
    :param str username: Username for which the password is reset
    :return bool: True if password has been reset
    """
    # Encrypt password before persisting
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

    # Update password
    try:
        user = User.query.filter_by(username=username).first()
        user.password = hashed_password.decode()
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        raise

    return True


def disable_user(user_id):
    """
    Disable user

    :param user_id: Unique identifier for user

    :return bool: True if successful
    """
    try:
        user = db.session.query(User).filter_by(user_id=user_id).first()
        user.is_disabled = True
        db.session.flush()
        return True
    except:
        db.session.rollback()
        raise


def generate_token(obj, validity_sec=86400):
    """
    Create a signed and timed token for password reset
    :param obj: Object to store in the token
    :param validity_sec: Number of seconds the token is valid
    :return token: Signed and timed token
    """
    try:
        # Read salt from ENV if it exists
        salt = app.config["TOKEN_SALT"] if "TOKEN_SALT" in app.config else None
        # Create token from JWT_KEY and TOKEN_SALT that expires in validity_sec
        # Default validity is 24 hours
        serialized_token = Serializer(
            app.config["JWT_SECRET_KEY"], salt=salt, expires_in=validity_sec
        )
        # Decoding to get string of token
        token = serialized_token.dumps(obj).decode("utf-8")
        return token
    except Exception as e:
        raise


def add_password_reset_token(token, user_id):
    """
    Add password reset token to table
    :param token: User password reset token
    :param user_id: Unique identifier for user
    :return True: True if successful
    """
    try:
        password_reset_token = UserPasswordResetToken(token, user_id)
        db.session.add(password_reset_token)
        db.session.flush()
        return True
    except Exception as e:
        db.session.rollback()
        raise


def send_password_reset_email(email, username, token):
    """
    Send password reset email to user
    :param email: Recipient email address
    :param username: Username used for greeting in email
    :param token: Token attached to reset link
    :return True: True if successful
    """
    # TODO sent email here
    pass


def check_password_token_validity(token):
    """
    Check validity of password token and return content
    :param token: Password reset token
    :return email: email to reset password for
    """
    try:
        # Fetch token where is_valid is True
        token_row = UserPasswordResetToken.query.filter(
            and_(
                UserPasswordResetToken.token == token,
                UserPasswordResetToken.is_valid == True,
            )
        ).first()
        # Check if it is older than 24 hours
        if token_row:
            token_created_at = token_row.created_at
            if (datetime.datetime.now() - token_created_at).total_seconds() > 86400:
                return None
    except Exception as e:
        db.session.rollback()
        raise
    try:
        # If a valid token exists, deserialize it
        if token_row:
            salt = app.config["TOKEN_SALT"] if "TOKEN_SALT" in app.config else None
            token_serializer = Serializer(app.config["JWT_SECRET_KEY"])
            token_data = token_serializer.loads(token, salt)
            return token_data["email"]
        else:
            return None
    except Exception as e:
        return None


def deserialize_token(token):
    """
    Generic function to deserialize token and return content
    :param token: Token
    :return token data
    """
    try:
        if token:
            salt = app.config["TOKEN_SALT"] if "TOKEN_SALT" in app.config else None
            token_serializer = Serializer(app.config["JWT_SECRET_KEY"])
            token_data = token_serializer.loads(token, salt)
            return token_data
        else:
            return None
    except BadData as ex:
        raise InvalidJWTToken(f"Invalid token: {ex}")
    except Exception as e:
        return None


def invalidate_password_reset_token(token):
    """
    Invalidate password reset token after use
    :param token: Token to invalidate
    """
    try:
        token_row = UserPasswordResetToken.query.filter(
            UserPasswordResetToken.token == token
        ).first()
        token_row.is_valid = False
        token_row.used_at = datetime.datetime.now()
        db.session.flush()
        return True
    except Exception as e:
        db.session.rollback()
        raise


def generate_qr_code(user_id, user_email):
    """
    Generate an MFA QR code for a user
    :param user_id: ID for user
    :param user_email: Email for user
    :return QRCode: QR Code for MFA
    """
    try:
        user = User.query.filter(User.user_id == user_id).first()
        if not user:
            raise Exception("Invalid User ID")
        if user.mfa_enabled:
            raise Exception("MFA is already activated")
        # Create MFA Secret
        secret_token = pyotp.random_base32()
        # Store it in DB as encrypted string
        # The Fernet secret needs to be urlsafe base64
        cipher_suite = Fernet((Config.MFA_SECRET_KEY).encode("utf-8"))
        encrypted_secret = cipher_suite.encrypt(secret_token.encode("utf-8"))
        user.mfa_secret = encrypted_secret
        secret_uri = pyotp.totp.TOTP(secret_token).provisioning_uri(
            name=user_email, issuer_name="Smart Assistance Systems"
        )
        qr_code = pyqrcode.create(secret_uri)
        db.session.flush()
        return qr_code
    except Exception as e:
        db.session.rollback()
        raise


def activate_mfa(user_id, otp):
    """
    Activate MFA for user
    :param user_id: ID for user
    :param otp: One time password for activating MFA
    :return bool: True if successful
    """
    try:
        user = User.query.filter(User.user_id == user_id).first()
        if not user:
            raise Exception("Invalid User ID")
        # Decrypt Secret token for MFA
        cipher_suite = Fernet((Config.MFA_SECRET_KEY).encode("utf-8"))
        if not user.mfa_secret:
            raise Exception("Token doesn't exist. Register with QR Code again")
        secret_token = cipher_suite.decrypt(user.mfa_secret)
        totp = pyotp.TOTP(secret_token)
        # Verify OTP
        if totp.verify(otp):
            user.mfa_enabled = True
            db.session.flush()
            return True
        else:
            raise Exception("Invalid OTP!")
    except Exception as e:
        db.session.rollback()
        raise


def deactivate_mfa(user_id):
    """
    Deactivate/disable MFA for a user
    :param user_id: ID for user
    :return bool: True if successful
    """
    try:
        user = User.query.filter(User.user_id == user_id).first()
        if not user:
            raise Exception("Invalid User ID")
        user.mfa_secret = None
        user.mfa_enabled = False
        db.session.flush()
        return True
    except Exception as e:
        db.session.rollback()
        raise


def get_mfa_status(user_id):
    """
    Get MFA status of user
    :param user_id: ID for user
    :return bool: true - if enabled, false - if disabled
    """
    user = User.query.filter(User.user_id == user_id).first()
    return user.mfa_enabled


def verify_mfa(user_id, otp):
    """
    Verifies MFA OTP for user
    :param user_id: ID for user
    :param otp: One time password for verifying MFA
    :return bool: True if successful
    """
    try:
        user = User.query.filter(User.user_id == user_id).first()
        if not user:
            raise Exception("Invalid User ID")
        # Decrypt Secret token for MFA
        cipher_suite = Fernet((Config.MFA_SECRET_KEY).encode("utf-8"))
        if not user.mfa_secret:
            raise Exception("Token doesn't exist. Register with QR Code again")
        if not user.mfa_enabled:
            raise Exception("MFA not activated")
        secret_token = cipher_suite.decrypt(user.mfa_secret)
        totp = pyotp.TOTP(secret_token)
        # Verify OTP
        if totp.verify(otp):
            return True
        else:
            raise Exception("Invalid OTP!")
    except Exception as e:
        db.session.rollback()
        raise


def get_user_details_google_auth(request, auth_code):
    """
    Get the user details from Google using auth code
    :request the http request
    :auth_code auth code received in the callback
    """
    # Try a total of 3 times if get request fails
    google_provider_cfg = token_response = {}
    total_retries = 3
    while True:
        total_retries -= 1
        # Get the google Auth endpoints from discovery url
        google_provider_cfg = requests.get(app.config["GOOGLE_DISCOVERY_URL"]).json()
        if google_provider_cfg:
            break
        else:
            if total_retries == 0:
                raise Exception("Exceeded retries for trying request")
            else:
                time.sleep(0.5)
    token_endpoint = google_provider_cfg["token_endpoint"]
    # The client library prepares the request to fetch the tokens
    token_url, headers, body = google_oauth_client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=auth_code,
    )
    # Get the token id from google using the secret credentials
    # Try a total of 3 times if post request fails
    total_retries = 3
    while True:
        total_retries -= 1
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(app.config["GOOGLE_CLIENT_ID"], app.config["GOOGLE_CLIENT_SECRET"]),
        )
        if token_response.json():
            break
        else:
            if total_retries == 0:
                raise Exception("Exceeded retries for trying request")
            else:
                time.sleep(0.5)

    # Fetching the token id from response
    google_oauth_client.parse_request_body_response(json.dumps(token_response.json()))
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = google_oauth_client.add_token(userinfo_endpoint)

    # Fetching the user response from google using token id.
    return get_user_response(uri, headers, body)


def get_user_response(uri, headers, body):
    """
    Fetching user details based on id token received from google
    uri,headers and body given by client
    :uri - request uri
    :headers request headers
    :body request body
    """
    # Try a total of 3 times if get request fails
    # Fetching the user details from google
    total_retries = 3
    userinfo_response = {}
    while True:
        total_retries -= 1
        userinfo_response = requests.get(uri, headers=headers, data=body)
        if userinfo_response.json():
            break
        else:
            if total_retries == 0:
                raise Exception("Exceeded retries for trying request")
            else:
                time.sleep(0.5)
    return userinfo_response.json()


def validate_email(email):
    """
    Validates email and returns boolean value
    :email - email to be validated
    """
    regex = (
        r"^[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*"
        "@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"
    )
    if re.match(regex, email):
        return True
    else:
        return False


def check_user_password_criteria(password):
    """
    Function to check password selection criteria
    :param str password: Password to check
    :return bool
    """
    # Must have atleast 8 chars, with atleast one symbol or number
    reg = "^(?=.*[a-z])(?=.*[A-Z])((?=.*[0-9])|(?=.*[!@#$%^&*]))(?=.{8,})"
    reg1 = "^(?=.*[!@#$%^&*])(?=.{8,})"
    reg3 = "^(?=.*[0-9])(?=.{8,})"
    # compiling regex
    pat = re.compile(reg)
    pat2 = re.compile(reg1)
    pat3 = re.compile(reg3)
    # searching regex
    mat = re.search(pat, password)
    mat2 = re.search(pat2, password)
    mat3 = re.search(pat3, password)
    # validating conditions
    if mat or mat2 or mat3:
        return True
    return False


def is_valid_uuid(uuid_to_check):
    try:
        uuid_obj = uuid.UUID(uuid_to_check)
        return True
    except Exception as e:
        _logger.exception(e)
        return False


def save_access_jit(jti, user_id):
    """save access token jti into database"""
    exist = AuthTokenBlacklist.query.filter_by(
        jti=jti, user_id=user_id, revoked=False
    ).first()
    if exist:
        return True

    auth_instance = AuthTokenBlacklist(
        jti=jti, created_at=datetime.datetime.now(), user_id=user_id, revoked=False
    )
    db.session.add(auth_instance)
    db.session.flush()
    return True


def check_user_exists(email):
    exist = User.query.filter(User.email == email).first()
    return exist


def get_users(query: PaginatorModel) -> list:
    users = (
        User.query.filter()
        .limit(query.per_page)
        .offset(query.page * query.per_page)
        .all()
    )
    users = [user.repr_name() for user in users]
    return users


def create_user_role_mapping(user_id, role_id):
    insert_cmd = UserRole.insert().values(user_id=user_id, role_id=role_id)
    db.session.execute(insert_cmd)
    db.session.flush()


def get_user(current_user):
    user = User.query.filter_by(user_id=current_user).first()
    return user.user_info()
