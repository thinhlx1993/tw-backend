from flask_restx import Resource
from flask_jwt_extended import (
    jwt_required
)
from flask_jwt_extended import get_jwt_identity

from src.v1.services import user_services
from src.version_handler import api_version_1_web

users_ns = api_version_1_web.namespace("users", description="User Functionalities")


class UserInfoOperations(Resource):
    @jwt_required
    def get(self):
        """
        User list route
        """
        current_user = get_jwt_identity()
        user_info = user_services.get_user(current_user)
        return user_info, 200


users_ns.add_resource(UserInfoOperations, "/info")
