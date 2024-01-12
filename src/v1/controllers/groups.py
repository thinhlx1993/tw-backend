"""Controller for groups."""

import logging
from flask_restx import fields, Resource
from flask_jwt_extended import get_jwt_claims
from src.services import groups_services
from src.utilities.custom_decorator import custom_jwt_required
from src.version_handler import api_version_1_web

# Create module log
_logger = logging.getLogger(__name__)

groups_ns = api_version_1_web.namespace(
    'groups',
    description='Groups Functionalities')

# Model for group creation
group_create_model = groups_ns.model(
    "group_create_model", {
        "group_name": fields.String(example="My Group"),
        "notes": fields.String(example="Some notes about the group")
    }
)

# Model for updating a group
group_update_model = groups_ns.model(
    "group_update_model", {
        "group_name": fields.String(example="New Group Name"),
        "notes": fields.String(example="Updated notes about the group")
    }
)

group_data_model = groups_ns.model(
    "group_data_model", {
        "group_id": fields.String(example="1234-5678-9101-1121"),
        "group_name": fields.String(example="My Group"),
        "notes": fields.String(example="Some notes about the group"),
        "created_at": fields.DateTime(example="2024-01-01T00:00:00"),
        "modified_at": fields.DateTime(example="2024-01-02T00:00:00")
    }
)

# Model for successful GET response (list of groups)
groups_list_response_model = groups_ns.model(
    "groups_list_response_model", {
        "groups": fields.List(fields.Nested(group_data_model)),
        "total": fields.Integer(example=1)
    }
)

# Model for successful POST, PUT, DELETE response
group_operation_response_model = groups_ns.model(
    "group_operation_response_model", {
        "message": fields.String(example="Operation successful"),
        "group": fields.Nested(group_data_model)
    }
)

# Model for internal server error response
internal_server_error_model = groups_ns.model(
    "internal_server_error_model", {
        "message": fields.String(example="Internal server error")
    }
)

# Model for unauthorized response
unauthorized_response_model = groups_ns.model(
    "unauthorized_response_model", {
        "message": fields.String(example="Not authorized")
    }
)


class GroupsController(Resource):
    """Class for /groups functionalities."""

    @groups_ns.response(200, "Success", groups_list_response_model)
    @groups_ns.response(401, "Authorization information is missing or invalid.", unauthorized_response_model)
    @groups_ns.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def get(self):
        """Retrieve list of groups"""
        groups = groups_services.get_all_groups()
        return groups, 200

    @groups_ns.response(200, "Group created successfully", group_operation_response_model)
    @groups_ns.expect(group_create_model)
    @groups_ns.response(401, "Authorization information is missing or invalid.", unauthorized_response_model)
    @groups_ns.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def post(self):
        """Create a new group"""
        try:
            data = groups_ns.payload
            group = groups_services.create_group(data)
            return {"group_id": group.group_id}, 200
        except Exception as e:
            _logger.debug(f"Data not valid: {e}")
            return {"message": "Data not valid"}, 400


class GroupDetailController(Resource):
    @groups_ns.expect(group_update_model)
    @groups_ns.response(200, "Group updated successfully", group_operation_response_model)
    @groups_ns.response(401, "Authorization information is missing or invalid.", unauthorized_response_model)
    @groups_ns.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def put(self, group_id):
        """Update a group"""
        try:
            data = groups_ns.payload
            group = groups_services.update_group(group_id, data)
            if group:
                return {"message": "Group updated successfully"}, 200
            return {"message": "Group not found"}, 404
        except Exception as e:
            _logger.debug(f"Error updating group: {e}")
            return {"message": "Data not valid or internal error"}, 400

    @groups_ns.response(200, "Group deleted successfully", group_operation_response_model)
    @groups_ns.response(401, "Authorization information is missing or invalid.", unauthorized_response_model)
    @groups_ns.response(500, "Internal Server Error", internal_server_error_model)
    @custom_jwt_required()
    def delete(self, group_id):
        """Delete a group"""
        try:
            result = groups_services.delete_group(group_id)
            if result:
                return {"message": "Group deleted successfully"}, 200
            return {"message": "Group not found"}, 404
        except Exception as e:
            _logger.debug(f"Error deleting group: {e}")
            return {"message": "Internal error"}, 500


groups_ns.add_resource(GroupsController, "")
groups_ns.add_resource(GroupDetailController, "/<string:group_id>")
