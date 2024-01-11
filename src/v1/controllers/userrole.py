"""Controller for /user_role"""

import logging
import uuid

from flask_restx import Resource, fields
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt_claims

from src import app
from src.services import user_services
from src.parsers import filter_parser
from src.services.user_services import check_is_administrator_user, check_is_operator_users
from src.version_handler import api_version_1_web
from src.utilities.custom_decorator import custom_jwt_required

# Create module log
_logger = logging.getLogger(__name__)

user_role_ns2 = api_version_1_web.namespace(
    'user_role', description='User role Functionalities')

# Internal error response model
internal_server_error_model = user_role_ns2.model(
    "internal_server_error_model", {
        "message": fields.String(example="Internal server error")
    }
)

# Unauthorized response model
unauthorized_response_model = user_role_ns2.model(
    "unauthorized_response_model", {
        "message": fields.String(example="Not authorized")
    }
)

user_role_dict = {
    "role_name": fields.String(example="role-name"),
    "role_id": fields.String(example=str(uuid.uuid4())),
    "role_description": fields.String(example="role-description")
}

user_role_pagination_dict = {
    "role_list": fields.List(
        fields.Nested(
            user_role_ns2.model('user_role_dict', user_role_dict)))
}

# User role search response model
user_role_search_response_ok_model = user_role_ns2.model(
    'user_role_search_response_ok_model', user_role_pagination_dict
)
user_role_search_bad_response_model = user_role_ns2.model(
    'user_role_search_bad_response_model', {
        "message": fields.String(example="Bad request. Invalid input")
    }
)


class UserRoleOperations(Resource):
    @custom_jwt_required()
    @user_role_ns2.response(200, "OK", user_role_search_response_ok_model)
    @user_role_ns2.response(400, "Bad Request", user_role_search_bad_response_model)
    @user_role_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_role_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def get(self):
        """Used to get list of user roles."""
        try:
            username = get_jwt_identity()
            claims = get_jwt_claims()
            kabam_user = user_services.check_kabam_users(username)
            roles = user_services.get_user_role_list()

            # check is admin
            is_administrator = check_is_administrator_user(claims.get('role'))
            is_operator_user = check_is_operator_users(claims.get('role'))
            if kabam_user or is_administrator:
                return {"role_list": roles}, 200
            elif is_operator_user:
                # this user does not have permissions to get list roles
                return {"role_list": []}, 200
            else:
                result = []
                role_exist = []

                # Add client Admin, Client Viewer, and Client Operator for the distributor 1 and distributor 2
                for role in roles:
                    if "client" in role["role_name"].lower():
                        result.append(role)
                        role_exist.append(role["role_name"].lower())

                # add current role for this user
                for user_role in claims.get("role"):
                    role_name = user_role.get("role_name")
                    if role_name.lower() in role_exist:
                        continue

                    result.extend(
                        [role for role in roles if role.get("role_name") == role_name]
                    )

            return {"role_list": result}, 200

        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


user_role_ns2.add_resource(UserRoleOperations, "/")
