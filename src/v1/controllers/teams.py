"""Controller for teams."""

import logging
from datetime import datetime
import json, uuid, os

from flask_restx import fields, reqparse, Resource
from flask_jwt_extended import get_jwt_claims
from flask_jwt_extended import get_jwt_identity
from flask import current_app

from src.enums.user_type import UserTypeEnums
from src.models import teams
from src.parsers import page_parser
from src.services import user_services, teams_services
from src.services import migration_services
from src.utilities.custom_decorator import custom_jwt_required
from src.version_handler import api_version_1_web
from src.enums.role_permissions import RoleId

# Create module log
_logger = logging.getLogger(__name__)

# Org fetch parser
org_fetch_parser = page_parser.copy()
# Setting possible columns to filter by, in the parser
columns = [m.key for m in teams.Teams.__table__.columns]
org_fetch_parser.replace_argument(
    'sort_by', type=str, choices=tuple(columns),
    help='Field to be sorted', location='args')
org_ns2 = api_version_1_web.namespace(
    'teams',
    description='Teams Functionalities')

# Internal error response model
internal_server_error_model = org_ns2.model(
    "internal_server_error_model", {
        "message": fields.String(example="Internal server error")
    }
)

# Unauthorized response model
unauthorized_response_model = org_ns2.model(
    "unauthorized_response_model", {
        "message": fields.String(example="Not authorized")
    }
)

user_id_parser = reqparse.RequestParser()
user_id_parser.add_argument('username', type=str,
                            help='username of the user', location='args')

# Ferch teamss dictionary example
org_fetch_dict = {
    "teams_id": fields.String(example=str(uuid.uuid4())),
    "teams_name": fields.String(example="Cognicept Systems - 1"),
    "owner": fields.String(example=str(uuid.uuid4())),
    "created_at": fields.String(example="2023-01-05 19:05:07.032291"),
    "updated_at": fields.String(example="2023-01-05 19:05:07.032291"),
    "is_disabled": fields.Boolean(example=True),
    "is_deleted": fields.Boolean(example=True)
}

org_fetch_response_ok_model = org_ns2.model(
    "org_fetch_response_ok_model", {
        "data": fields.List(fields.Nested(
            org_ns2.model("org_fetch_dict", org_fetch_dict)))
    }
)
org_fetch_bad_response_model = org_ns2.model(
    "org_fetch_bad_response_model", {
        "message": fields.String(example="Bad Request. Invalid input")
    }
)

# Org creation model
org_create_model = org_ns2.model(
    "org_create_model", {
        "teams_name": fields.String(example="Cognicept Systems")
    }
)

# Org creation response models
org_create_response_ok_model = org_ns2.model(
    "org_create_response_ok_model", {
        "teams_id": fields.String(example=str(uuid.uuid4()))
    }
)

org_create_bad_response_model = org_ns2.model(
    "org_create_bad_response_model", {
        "message": fields.String(example="Bad Request. Invalid input")
    }
)

# Org update model
org_row_model = {
    "teams_id": fields.String(
        example="b1267885-bc6f-46af-b3d3-1b41949cc833", required=True),
    "teams_name": fields.String(example="Cognicept Systems"),
    "owner": fields.String(example="bb34fc4d-8d63-4c38-b41d-71a314d7cb3a"),
    "created_at": fields.Date(example='2020-06-09 09:58:16.742037'),
    "updated_at": fields.Date(example='2020-06-09 09:58:16.742037'),
    "is_disabled": fields.Boolean(example=False),
    "is_deleted": fields.Boolean(example=False)
}

org_row_model = org_ns2.model("org_row_model", org_row_model)

# Org update response models
org_update_response_ok_model = org_ns2.model(
    "org_update_respoonse_ok_model", org_row_model
)

org_delete_row_model = org_ns2.model("org_delete_row_model", {
"message": fields.String(example="Deleted successfully")
})
# Org delete response models
org_delete_response_ok_model = org_ns2.model(
    "org_delete_response_ok_model", org_row_model
)


org_update_bad_response_model = org_ns2.model(
    "org_update_bad_response_model", {
        "message": fields.String(example="Bad Request. Invalid input")
    }
)

# Internal error response model
internal_server_error_model = org_ns2.model(
    "internal_server_error_model", {
        "message": fields.String(example="Failed to add user user@gmail.com")
    }
)

# Unauthorized response model
invlaid_token_response_model = org_ns2.model(
    "invlaid_token_response_model", {
        "message": fields.String(example="Token is invalid")
    }
)

# Org user add response models
teams_post_ok_model = org_ns2.model(
    'teams_post_ok_model', {
        'message': fields.String(
            example='User user@gmail.com has been added to Kabam')
    }
)

teams_post_bad_response_model = org_ns2.model(
    'user_create_bad_response_model', {
        'message': fields.String(example='Bad request. Invalid input')
    }
)

# Add user model
add_user_model = {
    "username": fields.String(example='thinhle.ict', required=True),
    "role_id": fields.String(example=str(uuid.uuid4()), required=True)
}

add_user_model = org_ns2.model("add_user_model", add_user_model)

# Delete user from org response models
delete_user_org_response_ok_model = org_ns2.model(
    "delete_user_org_response_ok_model", {
        'message': fields.String(example="User has been removed from org")
    }
)

delete_user_org_bad_response_model = org_ns2.model(
    "delete_user_org_bad_response_model", {
        'message': fields.String(example="Failed to remove user from org")
    }
)


class Teams(Resource):
    """Class for / functionalities."""

    @org_ns2.expect(org_fetch_parser)
    @org_ns2.response(200, "OK", org_fetch_response_ok_model)
    @org_ns2.response(400, "Bad Request", org_fetch_bad_response_model)
    @org_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @org_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def get(self):
        """Used to retrieve list of teams"""
        try:
            user_identity = get_jwt_identity()
        except Exception as e:
            _logger.debug(f"Not authorized: {e}")
            return {"Message", "Not authorized"}, 400
        try:
            args = org_fetch_parser.parse_args()
            # Pagination settings
            page = args.get("page", 1) if args.get("page") else None
            per_page = args.get("per_page") if args.get("per_page") else None
            # Sorts by 'teams_name' by default
            sort_by = str(args.get("sort_by")) if args.get(
                "sort_by") else "teams_name"
            # Sorts ascending by default
            sort_order = str(args.get("sort_order")) if args.get(
                "sort_order") else "asc"
            if sort_order.lower() not in ["asc", "desc"]:
                return {"message": "Invalid sort order"}, 400
            # Read any filters specified
            filters = json.loads(
                args.get("filter")) if args.get("filter") else None
            # Fetch results based on request parameters
            if user_identity == "admin":
                status, data = teams_services.fetch_teams(
                    page=page, per_page=per_page, sort_by=sort_by,
                    sort_order=sort_order, filters=filters)
            else:
                try:
                    claims = get_jwt_claims()
                    user_id = claims['user_id']
                except:
                    return {"message": "No user_id in JWT"}, 400
                status, data = teams_services.search_user_org_list(user_id,
                                                                   page=page, per_page=per_page, sort_by=sort_by,
                                                                   sort_order=sort_order, filters=filters)
            if not status:
                return data, 400
            result = {}
            result["data"] = data
            return result, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 500

    @org_ns2.expect(org_create_model)
    @org_ns2.response(200, "OK", org_create_response_ok_model)
    @org_ns2.response(400, "Bad Request", org_create_bad_response_model)
    @org_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @org_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def post(self):
        """Used to create teams"""
        try:
            data = org_ns2.payload
            user_claims = get_jwt_claims()
            user_id = user_claims['user_id']
        except Exception as e:
            _logger.debug(f"Data not valid: {e}")
            return {"message": "Data not valid"}, 400
        try:
            teams_name = data['teams_name']
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400

        status, teams_id, err_msg = teams_services.create_teams(
            teams_name, user_id)

        try:
            # Create teams and schema for user
            if status:
                # Create user teams mapping with is_default=False
                if user_services.create_user_teams_mapping(
                        user_id, teams_id, False):
                    teams_services.create_schema(teams_id)
                    # Setting migration path to created teams schema
                    current_app.config['GET_SCHEMAS_QUERY'] = (
                            current_app.config['GET_INDIVIDUAL_SCHEMA_QUERY']
                            + str(teams_id) + "'")
                    migration_services.upgrade_database()
                    # Resetting migration path to all teams
                    current_app.config['GET_SCHEMAS_QUERY'] = (
                        current_app.config['GET_ALL_SCHEMAS_QUERY'])
                else:
                    return {
                        "message": "Error creating user_org_mapping"}, 500
            elif err_msg:
                return {"message": err_msg}, 400
            else:
                return {"message": "Error creating teams"}, 500
        except Exception as err:
            _logger.exception(err)
            teams_services.rollback_teams_creation(
                teams_id, user_id
            )
            # Resetting migration path to all teams when
            # an exception occurs
            current_app.config['GET_SCHEMAS_QUERY'] = (
                current_app.config['GET_ALL_SCHEMAS_QUERY'])
            return {"message": str(err)}, 500

        # Setting search path
        try:
            if not user_services.create_user_role_mapping(
                    user_id, RoleId.Administrator.value, teams_id
            ):
                teams_services.rollback_teams_creation(teams_id, user_id)
                return {"message": "Error mapping role"}, 500

            migration_services.set_search_path(teams_id)

            # Create user preference with default page as robotops
            # and notifications_enabled as True
            if not user_services.create_user_preference(user_id):
                return {"message": "Error mapping role"}, 500
        except Exception as err:
            _logger.exception(err)
            teams_services.rollback_teams_creation(
                teams_id, user_id
            )
            return {"message": str(err)}, 500

        return {"teams_id": str(teams_id)}, 200

    @org_ns2.expect(org_row_model)
    @org_ns2.response(200, "OK", org_update_response_ok_model)
    @org_ns2.response(400, "Bad Request", org_update_bad_response_model)
    @org_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @org_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def put(self):
        """Used to update a teams"""
        request_data = org_ns2.payload
        # Only mandatory field
        try:
            teams_id = request_data['teams_id']
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400

        # Optional fields
        teams_name = (request_data['teams_name'] if
                      'teams_name' in request_data else None)
        owner = request_data.get('owner', None)
        created_at = request_data.get('created_at', None)
        updated_at = request_data.get('update_at', datetime.now().isoformat())
        is_disabled = request_data.get('is_disabled', None)
        is_deleted = request_data.get('is_deleted', None)
        try:
            update_dict = {
                'teams_id': teams_id,
                'teams_name': teams_name,
                'owner': owner,
                'created_at': created_at,
                'updated_at': updated_at,
                'is_disabled': is_disabled,
                'is_deleted': is_deleted
            }
            status, teams_row = teams_services.update_teams(
                update_dict)
            return teams_row, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


class TeamsByIDOperations(Resource):
    """Class for /teams/teams_id functionalities."""

    @org_ns2.response(200, "OK", org_row_model)
    @org_ns2.response(400, "Bad Request", org_update_bad_response_model)
    @org_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @org_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def get(self, teams_id):
        """Used to get a team"""
        # Optional fields
        exist_teams = teams_services.get_teams(teams_id)
        if not exist_teams:
            return {"message": "Team not found"}, 400
        return exist_teams.repr_name(), 200

    @org_ns2.response(200, "OK", org_delete_response_ok_model)
    @org_ns2.response(400, "Bad Request", org_update_bad_response_model)
    @org_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @org_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def delete(self, teams_id):
        """Used to delete a teams"""
        # Optional fields
        # check is default super admin org
        if teams_id == "06f992de-f34c-4362-99e8-ce66b35c6501":
            return {"message": "Cannot delete the Default teams"}, 400

        exist_teams = teams_services.get_teams(teams_id)
        user_claims = get_jwt_claims()
        user_id = user_claims['user_id']
        if not exist_teams:
            return {"message": "Team not found"}, 400
        if (user_id != UserTypeEnums.SuperAdmin.value and
                str(exist_teams.owner) != user_id):
            # user cannot delete other user teams
            return {"message": "You cannot delete other user's team"}, 400
        try:
            is_default = teams_services.check_is_default_org(teams_id, user_id=user_id)
            if not is_default:
                teams_services.rollback_teams_creation(teams_id=teams_id, user_id=None)
                return {"message": "Deleted successfully"}, 200
            return {"message": "Cannot delete the Default teams"}, 400
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


class TeamsUserOperations(Resource):
    """Class for /user functionalities."""

    @custom_jwt_required()
    @org_ns2.expect(add_user_model)
    @org_ns2.response(200, "OK", teams_post_ok_model)
    @org_ns2.response(400, "Bad Request", teams_post_bad_response_model)
    @org_ns2.response(
        401, "Token is invalid",
        invlaid_token_response_model)
    @org_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def post(self):
        """Used to add user to teams"""

        # Check mandatory field
        try:
            request_data = org_ns2.payload
            username = request_data['username']
            role_id = request_data['role_id']
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400

        claims = get_jwt_claims()
        teams_id = claims['teams_id']
        # Check user details
        try:
            user_details = user_services.check_user_exists(
                username=username)
            if not user_details:
                return {"message": f"{username} does not exist"}, 400
            user_details = user_services.row_to_dict(user_details)
        except Exception as e:
            _logger.debug(f"Could not fetch user details: {e}")
            return {"message": "Could not fetch user details"}, 400

        # Check if user already exists in the teams
        if user_services.check_user_teams_mapping(
                user_details['user_id'], teams_id):
            return {
                "message": "The user already exists in your teams!"
            }, 400

        # Add user to new org
        try:
            user_services.create_user_teams_mapping(
                user_details['user_id'], teams_id, False)
            user_services.create_user_role_mapping(
                user_details['user_id'], role_id, teams_id)
            user_services.create_user_preference(
                user_details['user_id'])
            org_name = teams_services.get_teams(teams_id).teams_name
            return {
                "message": f"User {user_details['username']} has been added to {org_name}"
            }, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": "Failed to add user " + str(err)}, 500

    @custom_jwt_required()
    @org_ns2.expect(user_id_parser)
    @org_ns2.response(200, "OK", delete_user_org_response_ok_model)
    @org_ns2.response(400, "Bad Request", delete_user_org_bad_response_model)
    @org_ns2.response(
        401, "Authorization information is missing or invalid.",
        unauthorized_response_model)
    @org_ns2.response(
        500, "Internal Server Error", internal_server_error_model)
    def delete(self):
        """Used to delete user from teams"""
        # Check mandatory field
        try:
            # request_data = org_ns.payload
            username = user_id_parser.parse_args()['username']
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400
        try:
            exist_user = user_services.get_username(username=username)
            if not exist_user:
                return {
                    "message": "The user does not exist!"
                }, 400
            user_id = exist_user.user_id
            # Check if user exists in teams
            user_claims = get_jwt_claims()
            current_org = user_claims['teams_id']
            if not user_services.check_user_teams_mapping(
                    user_id, current_org):
                return {
                    "message": "The user does not exist in your teams!"
                }, 400
            # Check if this is user's default org
            user_org_mapping = user_services.check_user_ownership(
                user_id, current_org)
            if (user_org_mapping and
                    str(user_org_mapping.teams_id) == current_org):
                return {
                    "message": "This user is owner of the teams and \
                    cannot be removed from this teams"
                }, 400
        except Exception as err:
            _logger.exception(err)
            return {
                "message": "Could not fetch user teams details"
                           + str(err)
            }, 400
        # Remove user from teams
        try:
            user_services.delete_user_teams_mapping(
                user_id, current_org)
            user_services.delete_user_preference(user_id)
            user_services.delete_user_role_mapping(user_id, current_org)
            return {
                "message": "User has been removed from org"
            }, 200
        except Exception as err:
            _logger.exception(err)
            return {
                "message": "Failed to remove user from org " + str(err)
            }, 400


org_ns2.add_resource(TeamsUserOperations, "/user")
org_ns2.add_resource(Teams, "/")
org_ns2.add_resource(TeamsByIDOperations, "/<string:teams_id>")
