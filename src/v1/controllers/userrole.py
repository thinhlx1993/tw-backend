"""Controller for /userrole"""

from flask_restx import Resource
from flask_jwt_extended import get_jwt_identity

from src.v1.services import user_services
from src.version_handler import api_version_1
from src.v1.utilities.custom_decorator import custom_jwt_required


user_role_ns = api_version_1.namespace(
    'userrole', description='User role  related operations')


class UserRoleList(Resource):
    # @user_role_ns.expect(company_parser)
    @custom_jwt_required()
    def get(self):
        """
        UserRole list route
        """
        # try:
        #     args = company_parser.parse_args()
        #     company_id = args['company_id']
        # except:
        #     return {"Message": "Required field missing"}, 400
        try:
            username = get_jwt_identity()
            kabam_user = user_services.check_kabam_users(username)
            roles = user_services.get_user_role_list()
            if kabam_user:
                return {'role_list': roles}, 200
            else:
                result = []
                for role in roles:
                    if 'client' in role['role_name'].lower():
                        result.append(role)
            return {'role_list': result}, 200

        except Exception as e:
            return {"Message": str(e)}, 400


# user_role_ns.add_resource(UserRoleList, "/list")
