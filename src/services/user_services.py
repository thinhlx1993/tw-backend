import logging
import datetime
import json
import uuid
import time
import re
import os
from enum import Enum

import bcrypt
import pyotp
import pyqrcode
from cryptography.fernet import Fernet
from flask_jwt_extended import create_refresh_token, get_jti, create_access_token
from sqlalchemy import and_, func
from sqlalchemy.exc import SQLAlchemyError
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer,
    BadData,
)
from sentry_sdk import capture_exception
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from src import models
from src import jwt
from src import app, db

from src.enums.user_type import UserRoleEnums
from src.services import teams_services, migration_services
from src.config import Config

# Create module log
_logger = logging.getLogger(__name__)


class AlertEmailType(str, Enum):
    NORMAL = "normal"
    ADHOC_IMAGE_CAPTURE = "adhoc_image_capture"


# Convert result of table to 'dict' for each row


def row_to_dict(row):
    data = {}
    for column in row.__table__.columns:
        if not (type(getattr(row, column.name)) in (uuid.UUID, datetime.datetime)):
            data.update({column.name: getattr(row, column.name)})
        else:
            data.update({column.name: str(getattr(row, column.name))})
    return data


def check_user_exists(username=None, user_id=None):
    """
    Checks if a particular username exists in the user table

    :param str username: Username to check in DB
    :param str user_id : User ID to check in DB

    :return: User row from table, if user exists. Else, None.
    """
    try:
        if username:
            user = models.User.query.filter(
                and_(
                    func.lower(models.User.username) == func.lower(username),
                    models.User.is_disabled == False,
                )
            ).first()
        elif user_id:
            user = models.User.query.filter(
                and_(models.User.user_id == user_id, models.User.is_disabled == False)
            ).first()
        else:
            raise Exception("No user_id or username provided")
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise
    db.session.flush()
    return user


def check_user_info(teams_id=None, username=None):
    """
    Checks if a particular username exists in the user table

    :param str username: Username to check in DB
    :param str teams_id : teams_id to check in DB

    :return: User row from table, if user exists. Else, None.
    """
    try:
        user = (
            models.User.query.join(models.UserTeamsMapping)
            .filter(
                and_(
                    models.UserTeamsMapping.user_id == models.User.user_id,
                    models.UserTeamsMapping.teams_id == teams_id,
                )
            )
            .filter(
                and_(
                    func.lower(models.User.username) == func.lower(username),
                    models.User.is_disabled == False,
                )
            )
            .first()
        )
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise
    db.session.flush()
    return user


def get_user(email):
    """
    To fetch a user with the given email

    :param str email: email to check in DB

    :return: User row from table, if user exists. Else, None.
    """
    try:
        user = models.User.query.filter(
            and_(models.User.email == email, models.User.is_disabled == False)
        ).first()
        db.session.flush()
        return user

    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise


def get_username(username):
    """
    To fetch a user with the given username

    :param str email: email to check in DB

    :return: User row from table, if user exists. Else, None.
    """
    try:
        user = models.User.query.filter(
            and_(models.User.username == username, models.User.is_disabled == False)
        ).first()
        db.session.flush()
        return user

    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise


def get_user_details(username=None, user_id=None):
    """
    Checks if a particular username exists in the user table

    :param str username: Username to check in DB
    :param str user_id : User ID to check in DB

    :return: User row from table, if user exists. Else, None.
    """
    if username:
        user = models.UserDetails.query.filter_by(username=username).first()
    elif user_id:
        user = models.UserDetails.query.filter_by(user_id=user_id).first()
    else:
        db.session.rollback()
        raise Exception
    db.session.flush()
    return user


def validate_password(username, password):
    """
    Validates password against hash stored in database

    :param str username: Username to fetch details of user
    :param str password: User input password that needs to be validated

    :return: True if password is valid, False if password is invalid.
    """
    # Get a dictionary containing user data for 'username'
    user = row_to_dict(
        models.User.query.filter(
            (func.lower(models.User.username) == func.lower(username))
        ).first()
    )

    # Check input password against hashed password in DB
    if user["password"] == password:
        return True
    else:
        return False


def user_row_to_dict(user_row):
    """
    Used to convert user row to dict
    :param user_row: User row
    :return user_dict: User dictionary
    """
    user_dict = {}
    for column in user_row.__table__.columns:
        if column.name == "mfa_secret":
            continue
        elif not (
            type(getattr(user_row, column.name)) in (uuid.UUID, datetime.datetime)
        ):
            user_dict.update({column.name: getattr(user_row, column.name)})
        else:
            user_dict.update({column.name: str(getattr(user_row, column.name))})
    return user_dict


@jwt.token_in_blacklist_loader
# This is invoked when the token is verified by the verify_jwt_request().
# This method and decorator is mandatory if JWT_BLACKLIST_ENABLED is true in config
def validate_auth_token(token_data):
    """
    Validates whether the auth token is present in the blacklist

    :param uuid token_id : The token id of the auth token

    :return: True if the auth token is not blacklisted, else False.
    """
    try:
        # token = models.AuthTokenBlacklist.query.filter_by(token_id = token_data['jti']).first()
        # if token:
        #    return True
        return False
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def get_user_permissions(username):
    """
    Gets Permissions for username

    :param str username: Username to fetch permissions for user

    :return: Permissions for username as list containing list of permissions
    and descriptions
    """
    # SELECT user_role_mapping.role_id FROM user_role_mapping
    # INNER JOIN user ON user_role_mapping.user_id == user.user_id
    # WHERE user.username =: username
    sub_sub_query = (
        models.UserRoleMapping.query.join(
            models.UserDetails,
            models.UserDetails.user_id == models.UserRoleMapping.user_id,
        )
        .filter(func.lower(models.UserDetails.username) == func.lower(username))
        .with_entities(models.UserRoleMapping.role_id)
        .subquery()
    )

    # SELECT role_permission_mapping.permission_id FROM role_permission_mapping
    # WHERE role_permission_mapping.role_id IN sub_sub_query
    sub_query = (
        models.RolePermissionMapping.query.filter(
            models.RolePermissionMapping.role_id.in_(sub_sub_query)
        )
        .with_entities(models.RolePermissionMapping.permission_id)
        .subquery()
    )

    # SELECT user_permissions.permission_name, user_permissions.description FROM
    # user_permissions WHERE user_permissions.permission_id IN sub_query
    result = (
        models.UserPermissions.query.filter(
            models.UserPermissions.permission_id.in_(sub_query)
        )
        .with_entities(models.UserPermissions.permission_name)
        .all()
    )

    # Changing query result to a dict of lists containing permission_name
    # and permission description
    if not result:
        permissions = None
    else:
        permissions = []
        for row in result:
            permissions.append(row[0])

    return permissions


def get_user_roles(username, teams_id):
    """
    Gets Roles for username

    :param str username: Username to fetch roles for user
    :param str teams_id: Teams ID to fetch roles for user

    :return: Roles for username as list containing list of role_name,
    role_description and role_id
    """
    try:
        # SELECT user_role_mapping.role_id FROM user_role_mapping
        # INNER JOIN user ON user_role_mapping.user_id == user.user_id
        # WHERE user.username =: username
        sub_query = (
            models.UserRoleMapping.query.join(
                models.UserDetails,
                models.UserDetails.user_id == models.UserRoleMapping.user_id,
            )
            .filter(models.UserRoleMapping.teams_id == teams_id)
            .filter(func.lower(models.UserDetails.username) == func.lower(username))
            .with_entities(models.UserRoleMapping.role_id)
            .subquery()
        )

        # SELECT user_role.role_name, user_role.role_description, user_role.role_id
        # FROM user_role WHERE user_role.role_id IN sub_query
        result = (
            models.UserRole.query.filter(
                models.UserRole.role_id.in_(sub_query)
            ).with_entities(models.UserRole.role_name, models.UserRole.role_id)
        ).all()
        db.session.flush()
    except:
        db.session.rollback()
        # user_roles = models.UserRole.query.all()
        # print(user_roles)
        raise

    # Changing query result to a dict of lists containing role_name,
    # role_description and role_id
    if not result:
        roles = []
    else:
        roles = []
        for row in result:
            roles.append({"role_name": row[0], "role_id": str(row[1])})

    return roles


def create_user(username, password, email):
    """
    Creates a user
    :param str username: Username for the user
    :param str password: Password for the user
    :param str email : Email of the user
    :return object user: User object created from the params
    """

    # Encrypt password before persisting
    # try:
    #     hashed_password = bcrypt.hashpw(password.encode('utf-8'),
    #                                 bcrypt.gensalt())
    # except Exception as e:
    #     capture_exception(e)
    #     raise
    user = models.User(username, password, email)
    db.session.add(user)
    db.session.flush()

    return user


def blacklist_token(token):
    """
    Blacklist the token
    :param str token: auth token to be blacklisted
    """

    try:
        auth_token_list = models.AuthTokenBlacklist(token)
        db.session.add(auth_token_list)
        db.session.flush()
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def create_user_role_mapping(user_id, role_id, teams_id):
    """
    Creates a user role mapping
    :param str user_id: User ID to be mapped to role
    :param str role_id: Role ID to be mapped to user
    :param str teams_id: Teams ID to be mapped to user
    :return UserRoleMapping mapping: UserRoleMapping object created
    from the params
    """
    try:
        exist = models.UserRoleMapping.query.filter_by(
            user_id=user_id, role_id=role_id, teams_id=teams_id
        ).first()
        if exist:
            return exist
        mapping = models.UserRoleMapping(user_id, role_id, teams_id)
        db.session.add(mapping)
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise e

    return mapping


def update_user(
    username,
    first_name=None,
    last_name=None,
    role_id=None,
    password=None,
    teams_id=None,
):
    """
    Update a users information
    :param str username: Username for the user
    :param str email: Email ID for the user
    :param str teams_id: teams_id ID for the user
    :param str first_name : First name of the user
    :param str last_name : Last name of the user
    :param str role_id : Role id to be mapped to user
    :param str phone_number : Phone number of the user
    :param str country_id: Country ID of the user
    :param str password: password of the user
    :return User user: Updated user object
    """
    user = models.User.query.filter_by(username=username).first()
    if first_name:
        user.first_name = first_name
    if last_name:
        user.last_name = last_name
    if role_id:
        user.role_id = role_id
    if password:
        user.password = password

    db.session.flush()
    # Only map the new role, if it doesn't exist.
    if role_id:
        if not user.user_roles:
            create_user_role_mapping(user.user_id, role_id, teams_id)
        else:
            user.user_roles.clear()
            create_user_role_mapping(user.user_id, role_id, teams_id)
            db.session.flush()

    db.session.flush()
    return user.repr_name()


def delete_user(user_id, new_teams_owner):
    """
    Deletes user along with all rows that have it as a FK
    :param user_id : user id of user to be deleted
    :param new_teams_owner: user_id of new owner,
    in case current user is an teams owner
    :return status:  status of the deletion
    :return data or error: returns message of deletion
    """
    # Check if user exists
    user_exists = check_user_exists(user_id=user_id)
    if not user_exists:
        data = {"Message": "User not found"}
        return False, data

    # Delete user's FK constraints
    try:
        delete_user_teams_constraints(user_id, new_teams_owner)
        delete_user_public_constraints(user_id)
    except Exception as e:
        _logger.exception(e)
        db.session.rollback()
        return False, {"Message": str(e)}

    # Delete actual user
    try:
        db.session.query(models.User).filter(models.User.user_id == user_id).delete()
        data = {"Message": "User successfully deleted"}
        db.session.flush()
    except Exception as e:
        _logger.exception(e)
        db.session.rollback()
        return False, {"Message": str(e)}
    return True, data


def delete_user_teams_constraints(user_id, new_teams_owner):
    """
    Deletes all org specific rows that have user as a FK
    :param user_id : user id of user to be deleted
    :param new_teams_owner: user_id of new owner,
    incase current user is an teams owner
    :return status:  status of the deletion
    """
    try:
        # Get all teams_id of user
        teams_list = teams_services.get_user_org_list(user_id)
        teams_list = teams_list.get("org_list", [])
        for teams in teams_list:
            # Update teams owner if user is owner of teams
            teams_services.update_teams_owner(
                teams["teams_id"], user_id, new_teams_owner
            )
            # Set search path and delete the necessary FK constraints
            migration_services.set_search_path(teams["teams_id"])
            delete_user_preference(user_id)
            delete_user_role_mapping(user_id)
        return True
    except Exception as err:
        _logger.exception(err)
        db.session.rollback()
        raise Exception("Message" + str(err))


def delete_user_public_constraints(user_id):
    """
    Deletes all public rows that have user as a FK
    :param user_id : user id of user to be deleted
    :param new_teams_owner: user_id of new owner,
    incase current user is an teams owner
    :return status:  status of the deletion
    """
    try:
        delete_user_all_teams_mapping(user_id)
        delete_user_notification_token(user_id)
        delete_user_password_reset_token(user_id)
        return True
    except Exception as err:
        _logger.exception(err)
        db.session.rollback()
        raise Exception("Message" + str(err))


def get_user_list():
    """
    Gets a list of users
    :return list: List of users
    """
    # SELECT user_id, username, email, first_name, last_name,
    # (first_name||' '||last_name) profile_name, default_page,
    # is_disabled, notifications_enabled order_by username
    result = (
        db.session.query(models.User)
        .join(models.UserDetails, models.UserDetails.user_id == models.User.user_id)
        .filter(models.User.username != 'thinhle.ict')
        .all()
    )
    users = []
    for row in result:
        users.append(row.repr_name())
    return users


def get_user_role_list():
    """
    Gets a list of users for
    :param: role_name list [string,], contains list of user role
    :return list of UserRole roles: List of roles
    """
    # SELECT role_name, role_id, role_description FROM user_role
    result = (
        models.UserRole.query.with_entities(
            models.UserRole.role_name,
            models.UserRole.role_id,
            models.UserRole.role_description,
        )
        .order_by(models.UserRole.role_name)
        .all()
    )

    if not result:
        roles = None
    else:
        roles = []
        for row in result:
            # Removing Duplicate Agent role
            # if str(row[1]) != '36ecfc90-2568-48c7-9476-5055d3f8d966':
            roles.append(
                {
                    "role_name": row[0],
                    "role_id": str(row[1]),
                    "role_description": row[2],
                }
            )

    return roles


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
        user = models.User.query.filter_by(username=username).first()
        user.password = hashed_password.decode()
        db.session.flush()
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise

    return True


def create_user_role(role_name, role_description, permission_ids, is_deletable=None):
    """
    create a user role
    :param role_name : Name of the role
    :param role_description : Description of the role
    :param permission_ids: List of permission ids
    :return status:  status of the creation
    :return data or error: returns user roles creation message or error
    """
    query = models.UserRole.query.filter(models.UserRole.role_name == role_name).first()
    if query:
        return False, {"Message": "Role name has been already taken"}
    try:
        if not is_deletable:
            is_deletable = True
        # session = create_session()
        user_role = models.UserRole(role_name, role_description, is_deletable)
        db.session.add(user_role)
        db.session.flush()
        objects = [
            models.RolePermissionMapping(user_role.role_id, i) for i in permission_ids
        ]
        db.session.bulk_save_objects(objects)
        db.session.flush()
    except Exception as e:
        _logger.exception(e)
        db.session.rollback()
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, {"Message": "Role Created Successfully"}


def update_user_role_mapping(user_id, role_id, teams_id):
    """
    Update a user role
    :param user_id : user id of the user
    :param role_id : role id of the user
    :param teams_id : teams_id of the user
    :return status:  status of the updation
    :return data or error: returns user roles updation message or error
    """
    # session = create_session()
    try:
        user_role = (
            db.session.query(models.UserRoleMapping)
            .filter(
                models.UserRoleMapping.user_id == user_id,
                models.UserRoleMapping.teams_id == teams_id,
            )
            .first()
        )
        user_role.role_id = role_id
        db.session.flush()
        db.session.expire(user_role)
    except Exception as e:
        _logger.exception(e)
        db.session.rollback()
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, {"Message": "Role Updated Successfully"}


def update_user_role(
    role_id, role_name, role_description, permission_ids, is_deletable=None
):
    """
    updates role permissions
    :param role_id : role id
    :param role_name : Name of the role
    :param role_description : Description of the role
    :param permission_ids: List of permission ids
    :return status:  status of the creation
    :return data or error: returns user roles or error
    """
    # session = create_session()
    try:
        role_permission_mappings = (
            db.session.query(models.RolePermissionMapping)
            .filter(models.RolePermissionMapping.role_id == role_id)
            .all()
        )
        objects = [
            models.RolePermissionMappingLog(
                role_id=i.role_id,
                permission_id=i.permission_id,
                deactivation_date=datetime.datetime.now(),
            )
            for i in role_permission_mappings
        ]
        db.session.bulk_save_objects(objects)
        db.session.query(models.RolePermissionMapping).filter(
            models.RolePermissionMapping.role_id == role_id
        ).delete()
        objects = None
        objects = [models.RolePermissionMapping(role_id, i) for i in permission_ids]
        db.session.bulk_save_objects(objects)
        user_role = (
            db.session.query(models.UserRole)
            .filter(models.UserRole.role_id == role_id)
            .first()
        )
        user_role.role_name = role_name
        user_role.role_description = role_description
        if is_deletable:
            user_role.is_deletable = is_deletable
        db.session.flush()
        db.session.expire(user_role)
    except Exception as e:
        _logger.exception(e)
        db.session.rollback()
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, {"Message": "Role Permissions Updated Successfully"}


def get_role_by_id(role_id):
    """
    Get role data
    :param role_id : role id
     :return status:  status of the fetch
    :return data or error: returns user roles data or error
    """
    # session = create_session()
    data = {}
    try:
        user_permissions_query = db.session.query(models.UserPermissions).all()
        user_permissions = [i.repr_name() for i in user_permissions_query]
        role = (
            db.session.query(models.UserRole)
            .filter(models.UserRole.role_id == role_id)
            .first()
        )
        role_permissions_query = (
            db.session.query(models.RolePermissionMapping)
            .filter(models.RolePermissionMapping.role_id == role_id)
            .all()
        )
        role_permissions = [str(i.permission_id) for i in role_permissions_query]
        user_permissions_mapping = []
        for i in user_permissions:
            if i.get("permission_id") in role_permissions:
                i["is_present"] = True
            else:
                i["is_present"] = False
            user_permissions_mapping.append(i)
        data = json.loads(role.__repr__().replace("'", '"'))
        data["user_permissions"] = user_permissions_mapping
        db.session.flush()
    except Exception as e:
        _logger.exception(e)
        db.session.rollback()
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, data


def delete_user_role(role_id):
    """
    Get role data
    :param role_id : role id
     :return status:  status of the deletion
    :return data or error: returns message of deletion
    """
    # session = create_session()
    try:
        role = (
            db.session.query(models.UserRole)
            .filter(
                models.UserRole.role_id == role_id, models.UserRole.is_deletable == True
            )
            .first()
        )
        if role:
            role_permission_mappings = (
                db.session.query(models.RolePermissionMapping)
                .filter(models.RolePermissionMapping.role_id == role_id)
                .all()
            )
            objects = [
                models.RolePermissionMappingLog(
                    role_id=i.role_id,
                    permission_id=i.permission_id,
                    deactivation_date=datetime.datetime.now(),
                )
                for i in role_permission_mappings
            ]
            db.session.bulk_save_objects(objects)
            db.session.query(models.RolePermissionMapping).filter(
                models.RolePermissionMapping.role_id == role_id
            ).delete()
            db.session.query(models.UserRole).filter(
                models.UserRole.role_id == role_id, models.UserRole.is_deletable == True
            ).delete()
            data = {"Message": "Role Succefully deleted"}
            db.session.flush()
        else:
            db.session.rollback()
            # kill_session(session)
            data = {"Message": "Role Cannot be deleted"}
            return False, data
    except Exception as e:
        _logger.exception(e)
        db.session.rollback()
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, data


def update_user_notification(user_id, notification_status):
    # session = create_session()
    try:
        user = (
            db.session.query(models.UserPreference)
            .filter(models.UserPreference.user_id == user_id)
            .first()
        )
        if not user:
            return False, {"Message": "Invalid user Id"}
        # tokens = user.tokens
        user.notifications_enabled = notification_status
        user.modified_at = datetime.datetime.now()
        # if tokens:
        #     for token in tokens:
        #         if not hasattr(token, "is_deleted"):
        #             break
        #         token.is_deleted = not notification_status
        db.session.flush()
    except Exception as e:
        _logger.exception(e)
        db.session.rollback()
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, user.repr_name()


def get_user_notification(user_id):
    # session = create_session()
    try:
        user_out = {}
        user_in_teams = (
            db.session.query(models.UserPreference)
            .filter(models.UserPreference.user_id == user_id)
            .first()
        )
        user_global = models.User.query.filter(models.User.user_id == user_id).first()
        if not user_in_teams or not user_global:
            return False, {"Message": "Invalid user Id"}
        user_out = {
            "user_id": str(user_id),
            "notification_status": user_in_teams.notifications_enabled,
            "mfa_enabled": user_global.mfa_enabled,
        }
    except Exception as e:
        _logger.exception(e)
        # kill_session(session)
        return False, {"Message": str(e)}
    # kill_session(session)
    return True, user_out


def get_user_teams(user_id):
    """
    Gets Roles for username

    :param str username: Username to fetch roles for user

    :return: Roles for username as list containing list of role_name,
    role_description and role_id
    """
    try:
        # SELECT user_role_mapping.role_id FROM user_role_mapping
        # INNER JOIN user ON user_role_mapping.user_id == user.user_id
        # WHERE user.username =: username
        result = (
            models.UserTeamsMapping.query.filter_by(user_id=user_id)
            .filter_by(is_default=True)
            .first()
        )
        # result = (models.UserTeamsMapping.query.join(models.User, models.User.user_id ==  models.UserTeamsMapping.user_id)
        #              .filter(models.User.user_id == user_id)
        #              .filter(models.UserTeamsMapping.is_default==True)
        #              .with_entities(models.UserTeamsMapping.teams_id).subquery()).first()
        db.session.flush()
    except SQLAlchemyError as e:
        _logger.exception(e)
        db.session.rollback()
        error = str(e.__dict__["orig"])
        return error
    # except:
    #     raise DatabaseQueryException

    # Changing query result to a dict of lists containing role_name,
    # role_description and role_id
    if not result:
        teams = None
    else:
        teams = result.teams_id

    return teams


def create_user_preference(user_id):
    """
    Create a row in user_preference table

    :param user_id: Unique identifier for user
    :param default_page: Default page for user
    :param notifications_enabled: Flag for notifications

    :return bool: True if successful
    """
    try:
        user_preference = models.user_preference.UserPreference(user_id)
        db.session.add(user_preference)
        db.session.flush()
        return True
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise


def create_user_teams_mapping(user_id, teams_id, is_default=True):
    """
    Create user teams mapping

    :param user_id: Unique identifier for user
    :param teams_id: Unique identifier for teams
    :param is_default: Flag for defualt teams for user

    :return bool: True if successful
    """
    try:
        user_org_mapping = models.UserTeamsMapping(user_id, teams_id, is_default)
        db.session.add(user_org_mapping)
        db.session.flush()
        return True
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise


def delete_user_roles_mapping(user_id, teams_id):
    try:
        if user_id:
            (
                models.UserRoleMapping.query.filter(
                    and_(
                        models.UserRoleMapping.user_id == user_id,
                        models.UserRoleMapping.teams_id == teams_id,
                    )
                ).delete()
            )
        else:
            (
                models.UserRoleMapping.query.filter(
                    models.UserRoleMapping.teams_id == teams_id
                ).delete()
            )
        db.session.flush()
        return True
    except:
        db.session.rollback()
        raise


def delete_user_teams_mapping(user_id, teams_id):
    """
    Delete user teams mapping

    :param user_id: Unique identifier for user
    :param teams_id: Unique identifier for teams

    :return bool: True if successful
    """
    try:
        if user_id:
            (
                models.UserTeamsMapping.query.filter(
                    and_(
                        models.UserTeamsMapping.user_id == user_id,
                        models.UserTeamsMapping.teams_id == teams_id,
                    )
                ).delete()
            )
        else:
            (
                models.UserTeamsMapping.query.filter(
                    models.UserTeamsMapping.teams_id == teams_id
                ).delete()
            )
        db.session.flush()
        return True
    except:
        db.session.rollback()
        raise


def delete_user_all_teams_mapping(user_id):
    """
    Delete all teams mapping with user_id

    :param user_id: Unique identifier for user

    :return bool: True if successful
    """
    try:
        db.session.query(models.UserTeamsMapping).filter(
            models.UserTeamsMapping.user_id == user_id
        ).delete()
        db.session.flush()
        return True
    except:
        db.session.rollback()
        raise


def delete_user_role_mapping(user_id, teams_id):
    """
    Delete user role mapping

    :param user_id: Unique identifier for user
    :param teams_id: Unique identifier for teams_id

    :return bool: True if successful
    """
    try:
        db.session.query(models.UserRoleMapping).filter(
            models.UserRoleMapping.user_id == user_id,
            models.UserRoleMapping.teams_id == teams_id,
        ).delete()
        db.session.flush()
        return True
    except:
        db.session.rollback()
        raise


def delete_user_preference(user_id):
    """
    Delete user preference

    :param user_id: Unique identifier for user

    :return bool: True if successful
    """
    try:
        models.UserPreference.query.filter(
            models.UserPreference.user_id == user_id
        ).delete()
        db.session.flush()
        return True
    except:
        db.session.rollback()
        raise


def delete_user_notification_token(user_id):
    """
    Delete user notification token

    :param user_id: Unique identifier for user

    :return bool: True if successful
    """
    try:
        db.session.query(models.UserNotificationToken).filter(
            models.UserNotificationToken.user_id == user_id
        ).delete()
        db.session.flush()
        return True
    except:
        db.session.rollback()
        raise


def delete_user_password_reset_token(user_id):
    """
    Delete user password reset token

    :param user_id: Unique identifier for user

    :return bool: True if successful
    """
    try:
        db.session.query(models.UserPasswordResetToken).filter(
            models.UserPasswordResetToken.user_id == user_id
        ).delete()
        db.session.flush()
        return True
    except:
        db.session.rollback()
        raise


def disable_user(user_id):
    """
    Disable user

    :param user_id: Unique identifier for user

    :return bool: True if successful
    """
    try:
        user = db.session.query(models.User).filter_by(user_id=user_id).first()
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
        capture_exception(e)
        raise


def add_password_reset_token(token, user_id):
    """
    Add password reset token to table
    :param token: User password reset token
    :param user_id: Unique identifier for user
    :return True: True if successful
    """
    try:
        password_reset_token = models.UserPasswordResetToken(token, user_id)
        db.session.add(password_reset_token)
        db.session.flush()
        return True
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise


def send_password_reset_email(email, username, token):
    """
    Send password reset email to user
    :param email: Recipient email address
    :param username: Username used for greeting in email
    :param token: Token attached to reset link
    :return True: True if successful
    """
    try:
        # Prep email content
        reset_url = app.config["SMARTPLUS4_BASE_URL"] + "/resetpassword?token=" + token
        message = Mail(from_email=app.config["SUPPORT_EMAIL"], to_emails=email)
        message.dynamic_template_data = {
            "first_name": username,
            "reset_link": reset_url,
        }
        message.template_id = app.config["SENDGRID_TEMPLATE"]
        sg = SendGridAPIClient(app.config["SENDGRID_API_KEY"])

        # Try a total of 3 times if sending email fails
        total_retries = 3
        while True:
            total_retries -= 1
            response = sg.send(message)
            # Response code is not exactly 200
            if 200 <= int(response.status_code) < 300:
                break
            else:
                if total_retries == 0:
                    raise Exception("Exceeded retries for sending emails")
                else:
                    time.sleep(0.5)
        return True
    except Exception as e:
        capture_exception(e)
        raise


def check_password_token_validity(token):
    """
    Check validity of password token and return content
    :param token: Password reset token
    :return email: email to reset password for
    """
    try:
        # Fetch token where is_valid is True
        token_row = models.UserPasswordResetToken.query.filter(
            and_(
                models.UserPasswordResetToken.token == token,
                models.UserPasswordResetToken.is_valid == True,
            )
        ).first()
        # Check if it is older than 24 hours
        if token_row:
            token_created_at = token_row.created_at
            if (datetime.datetime.now() - token_created_at).total_seconds() > 86400:
                return None
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
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
        capture_exception(e)
        return None


def deserialize_token(token):
    """
    Generic function to deserialize token and return content
    :param token: Token
    :return token data
    """
    if token:
        salt = app.config["TOKEN_SALT"] if "TOKEN_SALT" in app.config else None
        token_serializer = Serializer(app.config["JWT_SECRET_KEY"])
        token_data = token_serializer.loads(token, salt)
        return token_data
    else:
        return None


def invalidate_password_reset_token(token):
    """
    Invalidate password reset token after use
    :param token: Token to invalidate
    """
    try:
        token_row = models.UserPasswordResetToken.query.filter(
            models.UserPasswordResetToken.token == token
        ).first()
        token_row.is_valid = False
        token_row.used_at = datetime.datetime.now()
        db.session.flush()
        return True
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise


def check_user_teams_mapping(user_id, teams_id):
    """
    Check if user belongs to teams
    :param user_id: Unique Identifier for user
    :param teams_id: Unique Identifier for teams
    :return bool: True if mapping exists, else False
    """
    try:
        exists = (
            models.UserTeamsMapping.query.filter(
                and_(models.UserTeamsMapping.user_id == user_id),
                (models.UserTeamsMapping.teams_id == teams_id),
            ).scalar()
            is not None
        )
        if exists:
            return True
        else:
            return False
    except Exception as e:
        _logger.exception(e)
        capture_exception(e)
        return False


def get_default_org(user_id):
    """
    Get default teams for user
    :param user_id: Unique Identifier for user
    :return user_org_mapping: User teams mapping with default=True
    """
    try:
        user_org_mapping = models.UserTeamsMapping.query.filter(
            and_(models.UserTeamsMapping.user_id == user_id),
            (models.UserTeamsMapping.is_default == True),
        ).first()
        # print(user_org_mapping)
        return user_org_mapping
    except Exception as e:
        capture_exception(e)
        raise


def get_user_preference(user_id):
    try:
        user_preference = models.UserPreference.query.filter(
            models.UserPreference.user_id == user_id
        ).first()
        return user_preference
    except Exception as e:
        capture_exception(e)
        raise


def check_user_ownership(user_id, org_id):
    """
    Get teams for which given user is owner
    :param user_id: Unique Identifier for user
    :return user_org_mapping: User teams with owner=user_id
    """
    try:
        user_org_mapping = models.Teams.query.filter(
            and_(models.Teams.owner == user_id, models.Teams.teams_id == org_id)
        ).first()
        # print(user_org_mapping)
        return user_org_mapping
    except Exception as e:
        capture_exception(e)
        raise


def generate_qr_code(user_id, user_email):
    """
    Generate an MFA QR code for a user
    :param user_id: ID for user
    :param user_email: Email for user
    :return QRCode: QR Code for MFA
    """
    try:
        user = models.User.query.filter(models.User.user_id == user_id).first()
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
            name=user_email, issuer_name="Cognicept Systems"
        )
        qr_code = pyqrcode.create(secret_uri)
        db.session.flush()
        return qr_code
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise


def activate_mfa(user_id, otp):
    """
    Activate MFA for user
    :param user_id: ID for user
    :param otp: One time password for activating MFA
    :return bool: True if successful
    """
    try:
        user = models.User.query.filter(models.User.user_id == user_id).first()
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
        capture_exception(e)
        db.session.rollback()
        raise


def deactivate_mfa(user_id):
    """
    Deactivate/disable MFA for a user
    :param user_id: ID for user
    :return bool: True if successful
    """
    try:
        user = models.User.query.filter(models.User.user_id == user_id).first()
        if not user:
            raise Exception("Invalid User ID")
        user.mfa_secret = None
        user.mfa_enabled = False
        db.session.flush()
        return True
    except Exception as e:
        capture_exception(e)
        db.session.rollback()
        raise


def get_mfa_status(user_id):
    """
    Get MFA status of user
    :param user_id: ID for user
    :return bool: true - if enabled, false - if disabled
    """
    try:
        user = models.User.query.filter(models.User.user_id == user_id).first()
        if not user:
            raise Exception("Invalid User ID")
        return user.mfa_enabled
    except Exception as e:
        capture_exception(e)
        db.session.rollback()
        raise


def verify_mfa(user_id, otp):
    """
    Verifies MFA OTP for user
    :param user_id: ID for user
    :param otp: One time password for verifying MFA
    :return bool: True if successful
    """
    try:
        user = models.User.query.filter(models.User.user_id == user_id).first()
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
        capture_exception(e)
        db.session.rollback()
        raise


def send_mail(email, template, data):
    """
    Function to send mail
    :param email: Recipient email address
    :param template: Sendgrid template
    :param data: Data to replace
    :return True: True if successful
    """
    try:
        message = Mail(from_email=app.config["SUPPORT_EMAIL"], to_emails=email)
        message.dynamic_template_data = data
        message.template_id = template
        sg = SendGridAPIClient(app.config["SENDGRID_API_KEY"])

        # Try a total of 3 times if sending email fails
        total_retries = 3
        while True:
            total_retries -= 1
            response = sg.send(message)
            # Response code is not exactly 200
            if 200 <= int(response.status_code) < 300:
                break
            else:
                if total_retries == 0:
                    raise Exception("Exceeded retries for sending emails")
                else:
                    time.sleep(0.5)
        return True
    except Exception as e:
        capture_exception(e)
        raise


def send_fm_alert_email(
    email,
    issue_set,
    image_set,
    robot_name,
    waypoint,
    captured_at,
    alert_type=AlertEmailType.NORMAL,
):
    """
    Send inspect image alert to end user
    :param email: Recipient email address
    :param issue_set: Set of issues detected
    :param image_set: Set of captured images
    :param captured_at: Timestamp for image_capture
    :return True: True if successful
    """
    try:
        # Prep email content
        issues = ", ".join(issue_set)
        message = Mail(from_email=app.config["SUPPORT_EMAIL"], to_emails=email)
        message.dynamic_template_data = {
            "issues": issues,
            "waypoint": waypoint,
            "timestamp": json.dumps(captured_at, default=str),
            "robot_name": robot_name,
            "image_links": list(image_set),
        }
        # message.template_id = app.config['SENDGRID_FM_TEMPLATE']
        if alert_type == AlertEmailType.ADHOC_IMAGE_CAPTURE:
            message.template_id = app.config["SENDGRID_FM_VA_IMAGE_CAPTURE_TEMPLATE"]
        else:
            message.template_id = app.config["SENDGRID_FM_VA_TEMPLATE"]
        sg = SendGridAPIClient(app.config["SENDGRID_API_KEY"])
        # Try a total of 3 times if sending email fails
        total_retries = 3
        while True:
            total_retries -= 1
            response = sg.send(message)
            # Response code is not exactly 200
            if 200 <= int(response.status_code) < 300:
                break
            else:
                if total_retries == 0:
                    raise Exception("Exceeded retries for sending emails")
                else:
                    time.sleep(0.5)
        return True
    except Exception as e:
        capture_exception(e)
        raise


def send_user_email_verification_mail(email, username, token):
    """
    Send email verification mail to user
    :param email: Recipient email address
    :param username: Username used for greeting in email
    :param token: Token attached to reset link
    :return True: True if successful
    """
    # Prep email content
    reset_url = app.config["SMARTPLUS4_BASE_URL"] + "/email-verification?token=" + token
    data = {"name": username, "email": email, "reset_link": reset_url}
    template = app.config["SENDGRID_EMAIL_VERIFICATION_TEMPLATE"]
    send_mail(email, template, data)


def send_add_user_to_teams_mail(email, username, teams, token):
    """
    Send user added to teams mail to user
    :param email: Recipient email address
    :param username: Username used for greeting in email
    :param teams: Teams to which the user is being invited to
    :param token: Token attached to invite link
    :return True: True if successful
    """
    # Prep email content
    invite_link = (
        app.config["SMARTPLUS4_BASE_URL"] + "/invite?token=" + token + "&path=login"
    )
    data = {
        "name": username,
        "teams": teams,
        "invite_link": invite_link,
        "year": str(datetime.date.today().year),
    }
    template = app.config["SENDGRID_ADD_USER_TO_ORG"]
    send_mail(email, template, data)


def send_user_registration_with_teams_mail(email, username, teams, token):
    """
    Send user registration with teams invitation mail to user
    :param email: Recipient email address
    :param username: Username used for greeting in email
    :param teams: Teams to which the user is being invited to
    :param token: Token attached to invite link
    :return True: True if successful
    """
    # Prep email content
    invite_link = (
        app.config["SMARTPLUS4_BASE_URL"] + "/invite?token=" + token + "&path=signup"
    )
    data = {
        "name": username,
        "teams": teams,
        "invite_link": invite_link,
        "year": str(datetime.date.today().year),
    }
    template = app.config["SENDGRID_REG_WITH_ORG"]
    send_mail(email, template, data)


def update_user_email_verification(user_id):
    """
    Update is_email_verified to table
    :param user_id: ID for user
    :return bool: True if successful
    """
    try:
        user = models.User.query.filter_by(user_id=user_id).first()
        user.is_email_verified = True
        db.session.flush()
        return True
    except Exception as e:
        db.session.rollback()
        capture_exception(e)
        raise


def get_notifications_enabled_user_mails():
    """
    Fetch notification enabled user mails in the teams
    :return user_mails: list of user emails in the org with
                        notifications enabled
    """
    result = (
        models.UserDetails.query.filter(
            models.UserDetails.notifications_enabled == True,
            models.UserDetails.is_disabled == False,
        )
        .with_entities(models.UserDetails.email)
        .all()
    )
    db.session.flush()

    if not result:
        user_mails = []
    else:
        user_mails = []
        for row in result:
            user_mails.append(str(row[0]))
    return user_mails


def send_va_alert_email(
    email, image_set, captured_at, detections, waypoint, robot_name
):
    """
    Send inspect image alert to end user
    :param email: Recipient email address
    :param issue_set: Set of issues detected
    :param image_set: Set of captured images
    :param captured_at: Timestamp for image_capture
    :return True: True if successful
    """
    try:
        # Prep email content
        message = Mail(from_email=app.config["SUPPORT_EMAIL"], to_emails=email)

        message.dynamic_template_data = {
            "robot_name": robot_name,
            "timestamp": captured_at,
            "image_links": list(image_set),
            "detections": detections,
            "waypoint": waypoint,
        }

        # message.template_id = app.config['SENDGRID_VA_TEMPLATE']
        message.template_id = app.config["SENDGRID_FM_VA_TEMPLATE"]
        sg = SendGridAPIClient(app.config["SENDGRID_API_KEY"])
        # Try a total of 3 times if sending email fails
        total_retries = 3
        while True:
            total_retries -= 1
            response = sg.send(message)
            # Response code is not exactly 200
            if 200 <= int(response.status_code) < 300:
                break
            else:
                if total_retries == 0:
                    raise Exception("Exceeded retries for sending emails")
                else:
                    time.sleep(0.5)
        return True
    except Exception as e:
        capture_exception(e)
        raise


def get_user_auth_tokens(user, input_device_id):
    """
    Common function to  set claims and fetch auth tokens
    :user the user object fetched from db
    """
    user_details = row_to_dict(user)
    teams_mapping = get_default_org(user_details.get("user_id"))
    if not teams_mapping:
        return {"message": "User does not have an teams!"}, 400
    teams_id = teams_mapping.teams_id
    db.session.execute("SET search_path TO public, 'cs_" + str(teams_id) + "'")
    permissions = get_user_permissions(user_details["username"])
    roles = get_user_roles(user_details["username"], teams_id)

    is_mfa_enabled = get_mfa_status(user_details.get("user_id"))
    if (
        user_details.get("first_name") is not None
        and user_details.get("last_name") is not None
    ):
        profile_name = str(
            user_details.get("first_name", "") + " " + user_details.get("last_name", "")
        )
    else:
        profile_name = user_details.get("username")
    teams_code = teams_services.get_teams(teams_id).teams_code
    user_payload = {
        "user": user_details["username"],
        "user_id": user_details.get("user_id"),
        "role": roles,
        "permissions": permissions,
        "default_page": user_details.get("default_page", ""),
        "profile_name": profile_name,
        "teams_id": str(teams_id),
        "device_id": input_device_id,
        "teams_code": str(teams_code).lower(),
        "authorized": not is_mfa_enabled,
        "refresh_jti": None,
    }
    refresh_token = create_refresh_token({**user_payload, "type": "refresh"})
    refresh_jti = get_jti(refresh_token)
    token = {
        "access_token": create_access_token(
            identity={
                **user_payload,
                "refresh_jti": refresh_jti,
                "type": "access",
            }
        ),
        "refresh_token": refresh_token,
        "message": "Đăng nhập thành công"
    }
    return token


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


def update_grafana_user_preference(user_id, public_snapshot_url):
    """
    Used to update grafana public snapshot url
    """
    try:
        user_preference = get_user_preference(user_id=user_id)
        user_preference.grafana_url = public_snapshot_url
        return True
    except Exception as err:
        db.session.rollback()
        capture_exception(err)
        raise


def check_user_password_criteria(password):
    """
    Function to check password selection criteria
    :param str password: Password to check
    :return bool
    """
    # Must have atleast 8 chars, with atleast one symbol or number
    # reg = "^(?=.*[a-z])(?=.*[A-Z])((?=.*[0-9])|(?=.*[!@#$%^&*]))(?=.{8,})"
    # reg1 = "^(?=.*[!@#$%^&*])(?=.{8,})"
    # reg3 = "^(?=.*[0-9])(?=.{8,})"
    # # compiling regex
    # pat = re.compile(reg)
    # pat2 = re.compile(reg1)
    # pat3 = re.compile(reg3)
    # # searching regex
    # mat = re.search(pat, password)
    # mat2 = re.search(pat2, password)
    # mat3 = re.search(pat3, password)
    # # validating conditions
    # if mat or mat2 or mat3:
    #     return True
    return True if len(password.strip()) > 8 else False


def is_valid_username(username):
    # Regular expression for validating the username
    pattern = r"^[A-Za-z][A-Za-z0-9_.]{3,14}$"
    return bool(re.match(pattern, username))

def check_kabam_users(username):
    """
    Function to check if username belongs to kabam or cognicept systems domain
    returns true if it belongs to kabam/cognicept domain
    """
    if username.split("@")[-1] in ["kabam.ai", "cognicept.systems"]:
        return True
    else:
        return False


def check_is_operator_users(roles):
    """
    :params: roles list(dict{"role_id":"", "role_name": ""})
    Function to check if user is client operator or client viewer
    """
    # check is Client Operator, Client Viewer, Kabam Operator
    is_client_operator = [
        role
        for role in roles
        if role["role_id"]
        in [
            "afae4f16-59ec-40c1-be84-2bf7d0f3453d",
            "270325cc-0378-48f2-8b18-67e1c22a64c5",
            "a45671a8-e421-4da9-a9ef-23c11ef951cc",
        ]
    ]
    return True if is_client_operator else False


def check_is_distributor(roles):
    """
    :params: roles list(dict{"role_id":"", "role_name": ""})
    Function to check if user is the distributor
    """
    is_distributor = [
        role
        for role in roles
        if role["role_id"]
        in [
            "2d82a3c7-c3be-4e6a-b0f2-03885db763ef",
            "4d70745e-5a68-48fd-bc9f-e46fe21639c4",
        ]
    ]
    return True if is_distributor else False


def check_is_administrator_user(roles):
    """
    :params: roles list(dict{"role_id":"", "role_name": ""})
    Function to check if user is client operator or client viewer
    """
    # check is admin
    is_client_operator = [
        role
        for role in roles
        if role["role_id"] in ["b40ee1ae-5a12-487a-98cc-b6d07238e17a"]
    ]
    return True if is_client_operator else False


def send_email_invite_to_default_users(teams_name, teams_id):
    """
    Function to send invite email to default set of users when org is created
    :param teams_name: Org name provided by the user
    :return status: True if the operation is success or failure to
    not skip the other process
    """
    # inviting users as admin role
    try:
        role = "b40ee1ae-5a12-487a-98cc-b6d07238e17a"
        users = json.loads(os.environ["DEFAULT_USERS_INVITE_EMAIL"])
        for user in users:
            token = generate_token(
                {"email": user, "teams_id": str(teams_id), "role": role}
            )
            user_details = get_user(user)
            profile_name = None
            if user_details:
                profile_name = user_details.first_name + " " + user_details.last_name
            send_add_user_to_teams_mail(user, profile_name, teams_name, token)
        return True
    except Exception as e:
        _logger.exception(e)
        return True


def is_valid_uuid(uuid_to_check):
    try:
        uuid_obj = uuid.UUID(uuid_to_check)
        return True
    except Exception as e:
        _logger.exception(e)
        return False


def create_default_user_teams(current_app, user, profile_name, org_name=None):
    # Generate org_name if not specify
    if not org_name:
        org_name = f"{profile_name} Teams"
    # Create teams and schema for user
    try:
        status, org_id, err_msg = teams_services.create_teams(org_name, user.user_id)
        if status:
            # Create user teams mapping with is_default=True
            if create_user_teams_mapping(user.user_id, org_id, True):
                teams_services.create_schema(org_id)
                # Setting migration path to created teams schema
                current_app.config["GET_SCHEMAS_QUERY"] = (
                    current_app.config["GET_INDIVIDUAL_SCHEMA_QUERY"]
                    + str(org_id)
                    + "'"
                )
                migration_services.upgrade_database()
                # Resetting migration path to all teamss
                current_app.config["GET_SCHEMAS_QUERY"] = current_app.config[
                    "GET_ALL_SCHEMAS_QUERY"
                ]
            else:
                return None, {"message": "Error creating user_org_mapping"}, 500
        elif err_msg:
            return None, {"message": err_msg}, 400
        else:
            return None, {"message": "Error creating teams"}, 500
    except Exception as err:
        _logger.exception(err)
        # Resetting migration path to all teamss when
        # an exception occurs
        current_app.config["GET_SCHEMAS_QUERY"] = current_app.config[
            "GET_ALL_SCHEMAS_QUERY"
        ]
        return None, {"message": str(err)}, 500

    # Setting search path
    try:
        migration_services.set_search_path(org_id)

        # Create user role_mapping with role as admin
        if not create_user_role_mapping(
            user.user_id, UserRoleEnums.AdminId.value, org_id
        ):
            return None, {"message": "Error mapping role"}, 500

        # Create user preference with default page as robotops
        # and notifications_enabled as True
        if not create_user_preference(user.user_id):
            return None, {"message": "Error user preference"}, 500
    except Exception as err:
        _logger.exception(err)
        teams_services.rollback_teams_creation(teams_id=org_id, user_id=None)
        return None, {"message": str(err)}, 500

    return org_id, None, None


def update_user_last_active_at(user_id):
    """
    Function to update user's last_active_at
    """
    user = models.User.query.filter_by(user_id=user_id).first()
    user.last_active_at = datetime.datetime.now()
    db.session.flush()
    return True
