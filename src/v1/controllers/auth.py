from datetime import datetime, timedelta
import io
import random

from flask import request, send_file
from flask_pydantic import validate
from flask_restx import Resource, reqparse, fields
from flask_jwt_extended import (
    get_jwt_claims,
    create_refresh_token,
    get_jti,
    jwt_required,
    get_raw_jwt_header,
    get_raw_jwt,
    jwt_refresh_token_required,
)
from flask_jwt_extended import create_access_token, get_jwt_identity

from src.config import Config
from src.v1.data_model.user_model import user_login_model, user_getcode_model
from src.v1.enums.user_type import UserRoleMappingType
from src.v1.services import user_services, mailgun_services
from src.v1.utilities.custom_decorator import (
    custom_jwt_required,
    any_jwt_required,
)
from src.v1.validator.users_validator import (
    UserRegisterRequestBodyModel,
    UserLoginBodyModel,
)
from src.version_handler import api_version_1_web

auth_ns = api_version_1_web.namespace("auth", description="User Functionalities")


class UserGetCode(Resource):
    @auth_ns.expect(user_getcode_model)
    @validate()
    def post(self, body: UserLoginBodyModel):
        """User to get code"""
        input_email = body.email
        user_details = user_services.check_user_exists(email=input_email)
        if not user_details:
            # create a new one
            user_details = user_services.create_user(email=input_email)
        elif user_details.code_generated_at > datetime.utcnow() - timedelta(seconds=30):
            diff = (
                datetime.utcnow().timestamp()
                - user_details.code_generated_at.timestamp()
            )
            return {
                "msg": f"You can get a new code in {30 - int(diff)}s",
                "status": False,
            }, 200
        random_password = "".join(
            ["{}".format(random.randint(0, 9)) for num in range(0, 6)]
        )
        user_details.password = str(random_password)
        user_details.code_generated_at = datetime.utcnow()
        mailgun_services.send_mailgun_email(
            to=input_email,
            subject=f"MeetingX Sign in code: {str(random_password)}",
            text=f"This is your Sign in code: {str(random_password)}"
        )
        return {
            "msg": "Please check your mailbox to get verification code",
            "status": True,
        }, 200


class UserLogin(Resource):
    @auth_ns.expect(user_login_model)
    @validate()
    def post(self, body: UserLoginBodyModel):
        """
        User login route
        """
        input_email = body.email
        input_code = body.code

        user_details = user_services.check_user_exists(email=input_email)
        if not user_details:
            # create a new one
            return {
                "msg": "Username and code combination not valid",
                "status": False,
            }, 200

        if user_details.password != input_code:
            return {"Message": "Username and password combination not valid"}, 200

        is_mfa_enabled = user_services.get_mfa_status(user_details.user_id)
        user_payload = {
            "user_id": user_details.user_id,
            "authorized": not is_mfa_enabled,
            "refresh_jti": None,
            "type": "access",
        }
        refresh_token = create_refresh_token({**user_payload, "type": "refresh"})
        token = {
            "access_token": create_access_token(
                {
                    **user_payload,
                    "refresh_jti": get_jti(refresh_token),
                    "type": "access",
                }
            ),
            "refresh_token": refresh_token,
        }
        access_jit = get_jti(token["access_token"])
        user_services.save_access_jit(access_jit, user_details.user_id)
        user_details.last_activate_at = datetime.utcnow()
        return token, 200


class UserLogout(Resource):
    @jwt_required
    def delete(self):
        """
        JWT token blackout
        """
        jti = get_raw_jwt()["jti"]
        current_user = get_jwt_identity()
        user_services.blacklist_token(jti, current_user)
        return {"Message": "Successfully logged out"}, 200


class UserRefreshToken(Resource):
    @jwt_refresh_token_required
    def post(self):
        """
        JWT token refresh
        """
        user_id = get_jwt_identity()
        refresh_jti = get_raw_jwt()["jti"]
        user_payload = {
            "user_id": user_id,
            "authorized": True,
            "refresh_jti": refresh_jti,
            "type": "access",
        }
        access_token = create_access_token({**user_payload, "type": "access"})
        access_jti = get_jti(access_token)
        user_services.blacklist_token(access_jti, user_id)
        return {"access_token": access_token}, 200





class UserNotification(Resource):
    @custom_jwt_required()
    def get(self):
        """
        Get user notification status of user
        """
        try:
            user_id = user_id_parser.parse_args()["user_id"]
        except:
            return {"Message": "Required field missing"}, 400
        try:
            status, message = user_services.get_user_notification(user_id)
            if not status:
                return message, 400
            return message, 200
        except Exception as e:
            return {"Message": str(e)}, 400

    @custom_jwt_required()
    def put(self):
        """
        User notification update route
        """
        try:
            request_data = user_ns.payload
            user_id = request_data["user_id"]
            notification_status = request_data["notification_status"]
        except:
            return {"Message": "Required fields missing"}, 400
        try:
            status, message = user_services.update_user_notification(
                user_id, notification_status
            )
            if not status:
                return message, 400
            return {"Message": "Successfully updated notification"}, 200
        except Exception as e:
            return {"Message": str(e)}, 400


class UserRegistration(Resource):
    @validate()
    def post(self, body: UserRegisterRequestBodyModel):
        """
        User registration route
        """
        email = body.email
        password = body.password
        first_name = body.first_name
        last_name = body.last_name
        phone_number = body.phone_number
        username = body.username
        is_valid = user_services.validate_email(email)
        if not is_valid:
            return {"Message": "Invalid email address provided"}, 400

        # If username exists, abort.
        if user_services.check_user_exists(username=username):
            return {"Message": "User {} already exists".format(username)}, 400

        # Create user in user table
        new_user = user_services.create_user(
            username, email, password, first_name, last_name, phone_number
        )
        # Create user role_mapping with role as admin
        user_services.create_user_role_mapping(
            new_user.user_id, UserRoleMappingType.Users.value
        )

        return {"msg": f"User {username} has been created"}, 200


class UserForgotPassword(Resource):
    """
    Route to generate password reset URL
    """

    def post(self):
        try:
            request_data = user_ns.payload
            email = request_data["email"]
        except:
            return {"Message": "Required fields missing"}, 400

        # Validate user email
        try:
            user_details = user_services.check_user_exists(email)
            if not user_details:
                return {
                    "Message": "You will receive reset password email "
                    "if the user exists in our database. Redirecting to Login page."
                }, 200
            user_details = user_services.row_to_dict(user_details)
        except Exception as e:
            return {"Message": "Error finding user in DB " + str(e)}, 500

        # Create password reset token
        try:
            token = user_services.generate_token({"email": user_details["email"]})
        except Exception as e:
            return {"Message": "Error creating reset token " + str(e)}, 500

        # Add token to database
        try:
            user_services.add_password_reset_token(token, user_details["user_id"])
        except Exception as e:
            return {"Message": "Error adding token to DB " + str(e)}, 500

        # Send out email for password reset
        try:
            # Not all users have a first name.
            if user_details["first_name"]:
                username = user_details["first_name"]
            else:
                username = "User"
            user_services.send_password_reset_email(
                user_details["email"], username, token
            )
            return {
                "Message": "You will receive reset password email "
                "if the user exists in our database. Redirecting to Login page."
            }, 200
        except Exception as e:
            return {"Message": "Error sending password reset email " + str(e)}, 500


class UserValidatePasswordToken(Resource):
    """
    Route to validate password reset token
    """

    def post(self):
        try:
            request_data = user_ns.payload
            token = request_data["token"]
        except:
            return {"Message": "Required fields missing"}, 400

        # Check if token is valid
        try:
            if user_services.check_password_token_validity(token):
                return {"Message": "Token is valid!"}, 200
            else:
                return {"Message": "Token is invalid"}, 401
        except Exception as e:
            return {"Message": "Error checking token validity " + str(e)}, 500


class UserPasswordReset(Resource):
    """
    Route to consume token and reset password for user
    """

    def post(self):
        try:
            request_data = user_ns.payload
            token = request_data["token"]
            password = request_data["password"]
        except:
            return {"Message": "Required fields missing"}, 400

        # Check if token is valid
        try:
            email = user_services.check_password_token_validity(token)
            if not email:
                return {"Message": "Token is invalid"}, 401
        except Exception as e:
            return {"Message": "Error checking token validity " + str(e)}, 500

        # Reset password
        try:
            user_services.reset_password(email, password)
        except Exception as e:
            return {"Message": "Error resetting password " + str(e)}, 500

        # Invalidate token
        try:
            user_services.invalidate_password_reset_token(token)
            return {
                "Message": "Password has been reset! Redirecting to Login page."
            }, 200
        except Exception as e:
            return {"Message": "Error invalidating used token in DB " + str(e)}, 500


class UserSwitchOrganization(Resource):
    @custom_jwt_required()
    def post(self):
        """
        User switch organization route
        """
        try:
            request_data = user_ns.payload
            organization_id = request_data["organization_id"]
            claims = get_jwt_claims()
            username = get_jwt_identity()
            user_id = claims["user_id"]
        except:
            return {"Message": "Required field missing"}, 400

        if organization_id == claims["organization_id"]:
            # Return the same JWT from request header
            access_token = request.headers.get("Authorization").split(" ")[1]
            token = {"access_token": access_token}
            return token, 200

        try:
            # Added super admin functionality here. Using this user, we can access any organization. This user's credentials have to be SUPER SECRET.
            super_admin = Config.SUPER_ADMIN
            if super_admin == user_id:
                user_payload = {
                    "user": username,
                    "user_id": user_id,
                    "role": claims.get("role"),
                    "permissions": claims.get("permissions"),
                    "default_page": claims.get("default_page", ""),
                    "profile_name": claims.get("profile_name", ""),
                    "organization_id": str(organization_id),
                    "organization_code": str(
                        claims.get("organization_code", "")
                    ).lower(),
                    "authorized": claims.get("authorized"),
                    "refresh_jti": None,
                    "type": "access",
                }
                token = {"access_token": create_access_token(user_payload)}
                return token, 200
            elif user_services.check_user_organization_mapping(
                user_id, organization_id
            ):
                migration_services.set_search_path(organization_id)
                permissions = user_services.get_user_permissions(username)
                roles = user_services.get_user_roles(username)
                user_payload = {
                    "user": username,
                    "user_id": user_id,
                    "role": roles,
                    "permissions": permissions,
                    "default_page": claims.get("default_page", ""),
                    "profile_name": claims.get("profile_name", ""),
                    "organization_id": str(organization_id),
                    "organization_code": str(
                        claims.get("organization_code", "")
                    ).lower(),
                    "authorized": claims.get("authorized"),
                    "refresh_jti": None,
                    "type": "access",
                }
                token = {"access_token": create_access_token(user_payload)}
                return token, 200
            else:
                return {"Message": "User does not belong to organization"}, 400
        except Exception as e:
            return {"Message": str(e)}, 500


class UserCheck(Resource):
    @custom_jwt_required()
    def get(self, email):
        """
        Check if user exists
        """
        user = user_services.check_user_exists(username=email)
        user = user_services.user_row_to_dict(user) if user else {}

        # Remove password field before sending it as a response
        del user["password"]
        return user, 200


class UserGenerateMFAQRCode(Resource):
    @custom_jwt_required()
    def get(self):
        """
        Get QR code for MFA
        """
        try:
            user = get_jwt_claims()
            user_id = user["user_id"]
            user_email = user["user"]
            qr_code = user_services.generate_qr_code(user_id, user_email)
            # Creating an in memory stream for the PNG file
            buffer = io.BytesIO()
            qr_code.png(buffer, scale=5)
            buffer.seek(0)
            # Disabled caching of QR codes
            return send_file(buffer, mimetype="image/png", cache_timeout=-1)
        except Exception as e:
            return {"Message": str(e)}, 400


class UserMFAActivate(Resource):
    @custom_jwt_required()
    def post(self):
        """
        Activate MFA with OTP
        """
        try:
            request_data = user_ns.payload
            otp = request_data["otp"]
        except:
            return {"Message": "Required fields missing"}, 400
        try:
            user = get_jwt_claims()
            user_id = user["user_id"]
            if user_services.activate_mfa(user_id, otp):
                return {
                    "Message": "MFA has been activated",
                    "mfa_enabled": True,
                }, 200
        except Exception as e:
            return {"Message": str(e)}, 400


class UserMFADeactivate(Resource):
    @custom_jwt_required()
    def post(self):
        """
        Deactivate MFA for a user
        """
        try:
            user = get_jwt_claims()
            user_id = user["user_id"]
            if user_services.deactivate_mfa(user_id):
                return {
                    "Message": "MFA has been deactivated",
                    "mfa_enabled": False,
                }, 200
        except Exception as e:
            return {"Message": str(e)}, 400


class UserMFAVerify(Resource):
    @any_jwt_required()
    def post(self):
        """
        Verify MFA  OTP
        """
        try:
            request_data = user_ns.payload
            otp = request_data["otp"]
        except:
            return {"Message": "Required fields missing"}, 400
        try:
            user = get_jwt_claims()
            user_id = user["user_id"]
            if user_services.verify_mfa(user_id, otp):
                user_payload = {
                    "user": user["user"],
                    "user_id": user["user_id"],
                    "role": user.get("role"),
                    "permissions": user["permissions"],
                    "default_page": user["default_page"],
                    "profile_name": user["profile_name"],
                    "organization_id": user["organization_id"],
                    "organization_code": str(user["organization_code"]).lower(),
                    "authorized": True,
                    "refresh_jti": None,
                    "type": "access",
                }
                token = {"access_token": create_access_token(user_payload)}
                return token, 200
        except Exception as e:
            return {"Message": str(e)}, 400


auth_ns.add_resource(UserLogin, "/login")
auth_ns.add_resource(UserGetCode, "/code")
auth_ns.add_resource(UserLogout, "/logout")
auth_ns.add_resource(UserRefreshToken, "/refresh")
# auth_ns.add_resource(UserOperations, "/")
# auth_ns.add_resource(UserRegistration, "/registration")
# auth_ns.add_resource(UserForgotPassword, "/password/forgot")
# auth_ns.add_resource(UserValidatePasswordToken, "/password/validate")
# auth_ns.add_resource(UserPasswordReset, "/password/reset")
# auth_ns.add_resource(UserGenerateMFAQRCode, "/mfa/token")
# auth_ns.add_resource(UserMFAActivate, "/mfa/activate")
# auth_ns.add_resource(UserMFADeactivate, "/mfa/deactivate")
# auth_ns.add_resource(UserMFAVerify, "/mfa/verify")
