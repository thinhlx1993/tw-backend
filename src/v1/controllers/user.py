"""Controller for /user."""

import logging
import uuid

from flask import current_app
from flask import request, jsonify
from flask_restx import Resource, reqparse, fields
from flask_jwt_extended import get_raw_jwt, get_jwt_claims
from flask_jwt_extended import create_access_token, get_jwt_identity, get_jti
from flask_jwt_extended import create_refresh_token, jwt_refresh_token_required

from src.config import Config
from src import db
from src.enums.role_permissions import RoleName
from src.enums.user_type import UserTypeEnums, UserRoleEnums
from src.services import user_services, teams_services, migration_services
from src.version_handler import api_version_1_web
from src.services.teams_services import set_user_default_teams
from src.utilities.custom_decorator import custom_jwt_required

# Create module log
_logger = logging.getLogger(__name__)

user_ns2 = api_version_1_web.namespace("user", description="User Functionalities")

# Internal error response model
internal_server_error_model = user_ns2.model(
    "internal_server_error_model",
    {"message": fields.String(example="Internal server error")},
)

# Unauthorized response model
unauthorized_response_model = user_ns2.model(
    "unauthorized_response_model", {"message": fields.String(example="Not authorized")}
)

# Token expired response model
token_expired_response_model = user_ns2.model(
    "token_expired_response_model", {"message": fields.String(example="Token expired")}
)

blacklist = set()
user_parser = reqparse.RequestParser()
user_parser.add_argument(
    "username", type=str, help="Username of the user", location="args"
)
user_id_parser = reqparse.RequestParser()
user_id_parser.add_argument(
    "user_id", type=str, help="User id of the user", location="args"
)
dashboard_theme_parser = reqparse.RequestParser()
dashboard_theme_parser.add_argument(
    "theme", type=str, default="dark", help="Theme of the dashboard", location="args"
)
user_model = {
    "username": fields.String(example="someone"),
    "first_name": fields.String(example="John"),
    "last_name": fields.String(example="Doe"),
    "role_id": fields.String(example="270325cc-0378-48f2-8b18-67e1c22a64c5"),
}
create_user_model = {
    "username": fields.String(example="someone"),
    "first_name": fields.String(example="John"),
    "last_name": fields.String(example="Doe"),
    "phone_number": fields.String(example="+916655928947"),
    "password": fields.String(example="123#"),
    "role_id": fields.String(
        example="270325cc-0378-48f2-8b18-67e1c22a64c5", required=True
    ),
}

register_user_model = {
    "username": fields.String(example="new account", required=True),
    "first_name": fields.String(example="John"),
    "last_name": fields.String(example="Doe"),
    "role_id": fields.String(
        example="b40ee1ae-5a12-487a-98cc-b6d07238e17a", required=True
    ),
    "password": fields.String(example="12345#", required=True),
    "teams_name": fields.String(example="Default team", required=True),
}

user_row_dict = register_user_model.copy()
user_row_dict.pop("teams_name")
user_row_dict.update(
    {
        "user_id": fields.String(example=str(uuid.uuid4())),
        "notifications_enabled": fields.Boolean(example=True),
        "phone_number": fields.String(example="+91665592787"),
        "created_at": fields.String(example="2022-04-21 11:34:07.82"),
        "default_page": fields.String(example="robotops"),
        "username": fields.String(example="user@gmail.com"),
        "is_disabled": fields.Boolean(example=True),
    }
)

user_reset_password_model = user_ns2.model(
    "user_reset_password_model",
    {
        "old_password": fields.String(example="password", required=True),
        "new_password": fields.String(example="newpassword", required=True),
    },
)

google_login_parser = reqparse.RequestParser()
google_login_parser.add_argument("login", type=str, help="login", location="args")

callback_parser = reqparse.RequestParser()
callback_parser.add_argument("code", type=str, help="code", location="args")
callback_parser.add_argument("scope", type=str, help="scope", location="args")

# User login model
user_password_model = user_ns2.model(
    "login_model",
    {
        "username": fields.String(example="thinhle.ict", required=True),
        "password": fields.String(example="Admin@1234", required=True),
        "device_id": fields.String(example="ad26a5fd-b0ac-4a85-98ef-37c495c18012", required=False),
    },
)
user_register_model = user_ns2.model("user_register_model", register_user_model)
user_create_model = user_ns2.model("user_create_model", create_user_model)
user_update_model = user_ns2.model("user_update_model", user_model)
user_update_model.update({"password": fields.String(example="new password")})

user_notification_model = user_ns2.model(
    "user_notification_model",
    {
        "user_id": fields.String(example=str(uuid.uuid4()), required=True),
        "notification_status": fields.Boolean(example=True, required=True),
    },
)

forgot_password_model = user_ns2.model(
    "forgot_password_model",
    {"email": fields.String(example="user@cognicept.systems", required=True)},
)

validate_password_token_model = user_ns2.model(
    "validate_password_token_model",
    {"token": fields.String(example="eyJhbGciOiJIUA", required=True)},
)

# User email verification models
validate_user_email_verification_model = user_ns2.model(
    "validate_user_email_verification_model",
    {"token": fields.String(example="eyJhbGciOiJIUA", required=True)},
)

user_email_verification_ok_model = user_ns2.model(
    "user_email_verification_ok_model",
    {"message": fields.String(example="User email verified!")},
)
user_email_verification_bad_response_model = user_ns2.model(
    "user_email_verification_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

reset_password_model = user_ns2.model(
    "reset_password_model",
    {
        "token": fields.String(example="eyJhbGciOiJIUA", required=True),
        "password": fields.String(example="password", required=True),
    },
)

# User switch teams model
switch_org_model = {"teams_id": fields.String(example=str(uuid.uuid4()), required=True)}
switch_org_model = user_ns2.model("switch_org_model", switch_org_model)

user_invite_model = user_ns2.model(
    "user_invite_model",
    {
        "email": fields.String(example="user@cognicept.systems", required=True),
        "role": fields.String(example="b40ee1ae-5a12-487a-98cc-b6d07238e17a"),
    },
)

user_invite_ok_model = user_ns2.model(
    "user_invite_ok_model", {"message": fields.String(example="Invite mail sent!")}
)
user_invite_bad_response_model = user_ns2.model(
    "user_invite_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

user_mail_bad_response_model = user_ns2.model(
    "user_mail_bad_response_model",
    {"message": fields.String(example="Error sending mail")},
)

mfa_activate_model = user_ns2.model(
    "mfa_activate_model", {"otp": fields.String(example="248762")}
)

mfa_verify_model = user_ns2.model(
    "mfa_verify_model", {"otp": fields.String(example="426871")}
)

# User login response models
user_login_response_ok_model = user_ns2.model(
    "user_login_response_ok_model",
    {
        "access_token": fields.String(
            example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3MDUxMTkwNjYsIm5iZiI6MTcwNTExOTA2NiwianRpIjoiNjEyZDRiMWItYjQ0Ni00MzVmLTk5MTItZmZjYmM0YWRkZWVhIiwiZXhwIjoxNzA1NzIzODY2LCJpZGVudGl0eSI6InRoaW5obGUuaWN0IiwiZnJlc2giOmZhbHNlLCJ0eXBlIjoiYWNjZXNzIiwidXNlcl9jbGFpbXMiOnsidXNlcl9pZCI6IjhmM2VlODJkLWZhNDAtNDJjMS04NGNkLTJkYTIxNTkzN2M0MCIsInVzZXIiOiJ0aGluaGxlLmljdCIsInJvbGUiOlt7InJvbGVfbmFtZSI6ImFkbWluIiwicm9sZV9pZCI6ImI0MGVlMWFlLTVhMTItNDg3YS05OGNjLWI2ZDA3MjM4ZTE3YSJ9XSwicGVybWlzc2lvbnMiOm51bGwsImRlZmF1bHRfcGFnZSI6bnVsbCwicHJvZmlsZV9uYW1lIjoiVGhpbmggTGUiLCJ0ZWFtc19pZCI6IjA2Zjk5MmRlLWYzNGMtNDM2Mi05OWU4LWNlNjZiMzVjNjUwMSIsInRlYW1zX2NvZGUiOiJodXlfZHVjXzEiLCJhdXRob3JpemVkIjp0cnVlLCJyZWZyZXNoX2p0aSI6IjAxMGU0OTIzLWM0ODctNGVkMC05Y2FhLTEzMGIzMTM4MjUxNiJ9fQ.tf9oxCQtWyTdjNcS_jm8NR7hPI0KaqU3I07SyiCk69U"
        ),
        "refresh_token": fields.String(
            example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpYXQiOjE3MDUxMTkwNjYsIm5iZiI6MTcwNTExOTA2NiwianRpIjoiMDEwZTQ5MjMtYzQ4Ny00ZWQwLTljYWEtMTMwYjMxMzgyNTE2IiwiZXhwIjoxNzA3NzExMDY2LCJpZGVudGl0eSI6InRoaW5obGUuaWN0IiwidHlwZSI6InJlZnJlc2giLCJ1c2VyX2NsYWltcyI6eyJ0ZWFtc19pZCI6IjA2Zjk5MmRlLWYzNGMtNDM2Mi05OWU4LWNlNjZiMzVjNjUwMSIsInRlYW1zX2NvZGUiOiJodXlfZHVjXzEifX0.M8wU91mhQrTYyri5vcImxatUmovO37AFYy56nXHf18I"
        ),
    },
)

user_login_bad_response_model = user_ns2.model(
    "user_login_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

user_google_auth_redirect_model = user_ns2.model(
    "user_google_login_redirect_model", {"message": fields.String(example="Redirect")}
)

# User login response models
user_google_login_response_ok_model = user_ns2.model(
    "user_google_login_response_ok_model",
    {
        "access_token": fields.String(
            example="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI"
            "1NiJ9.eyJpYXQiOjE2NjM2Mzg2ODEsIm5iZiI6MTY2MzYzODY4MSwianRpIjoiNjhhZDV"
            "iMzAtYTY3OS00OTRjLThkMTEtMTdkYWYwNDAwYjEyIiwiZXhwIjoxNjY0MjQzNDgxLCJp"
            "ZGVudGl0eSI6InNvbWVvbmVAZ21haWwuY29tIiwiZnJlc2giOmZhbHNlLCJ0eXBlIjoiY"
            "WNjZXNzIiwidXNlcl9jbGFpbXMiOnsidXNlcl9pZCI6ImYyNjM5MGU2LTBlNWEtNDIzMC"
            "05ODlkLTc2YmE5MzBkZTU2YSIsInVzZXIiOiJzb21lb25lQGdtYWlsLmNvbSIsInJvbGU"
            "iOlt7InJvbGVfbmFtZSI6ImFkbWluIiwicm9sZV9kZXNjcmlwdGlvbiI6IkFkbWluaXN0"
            "cmF0b3Igb2YgdGhlIHN5c3RlbSIsInJvbGVfaWQiOiJiNDBlZTFhZS01YTEyLTQ4N2EtO"
            "ThjYy1iNmQwNzIzOGUxN2EifV0sInBlcm1pc3Npb25zIjpbeyJwZXJtaXNzaW9uX25hbW"
            "UiOiJyb2JvdG9wczp2aXNpdCIsImRlc2NyaXB0aW9uIjoiVmlzaXQgUm9ib3RvcHMgcGF"
            "nZSJ9LHsicGVybWlzc2lvbl9uYW1lIjoibG9nb3V0OnZpc2l0IiwiZGVzY3JpcHRpb24i"
            "OiJBYmxlIHRvIGxvZ291dCJ9LHsicGVybWlzc2lvbl9uYW1lIjoidGlja2V0czp2aXNpd"
            "CIsImRlc2NyaXB0aW9uIjoiVmlldyB0aWNrZXRzIHBhZ2UifSx7InBlcm1pc3Npb25fbm"
            "FtZSI6InJvYm90VGVsZW9wOnZpc2l0IiwiZGVzY3JpcHRpb24iOiJBY2Nlc3Mgcm9ib3Q"
            "gdGVsZW9wIGZlYXR1cmUifSx7InBlcm1pc3Npb25fbmFtZSI6ImRhc2hib2FyZDp2aXNp"
            "dCIsImRlc2NyaXB0aW9uIjoiVmlldyBkYXNoYm9hcmQgcGFnZSJ9LHsicGVybWlzc2lvb"
            "l9uYW1lIjoidXNlcjp2aXNpdCIsImRlc2NyaXB0aW9uIjoiVmlldyB1c2VyIGxpc3QifS"
            "x7InBlcm1pc3Npb25fbmFtZSI6InJvYm9vcHM6dmlzaXQiLCJkZXNjcmlwdGlvbiI6IlJ"
            "vYm90b3BzIHBhZ2UgdmlzaXQifSx7InBlcm1pc3Npb25fbmFtZSI6InNldHRpbmdzOnZp"
            "c2l0IiwiZGVzY3JpcHRpb24iOiJUbyB2aXNpdCBhbmQgbW9kaWZ5IHNldHRpbmdzIn0se"
            "yJwZXJtaXNzaW9uX25hbWUiOiJyb2JvdHM6dmlzaXQiLCJkZXNjcmlwdGlvbiI6IlZpZX"
            "cgcm9ib3QgbGlzdCJ9LHsicGVybWlzc2lvbl9uYW1lIjoic2l0ZXM6dmlzaXQiLCJkZXN"
            "jcmlwdGlvbiI6IlZpZXcgc2l0ZXMgbGlzdCJ9LHsicGVybWlzc2lvbl9uYW1lIjoid2F5"
            "cG9pbnQ6Y3JlYXRlIiwiZGVzY3JpcHRpb24iOiJDcmVhdGUgYSB3YXlwb2ludCJ9LHsic"
            "GVybWlzc2lvbl9uYW1lIjoid2F5cG9pbnQ6cmVhZCIsImRlc2NyaXB0aW9uIjoiR2V0IG"
            "Egd2F5cG9pbnQifSx7InBlcm1pc3Npb25fbmFtZSI6IndheXBvaW50OnVwZGF0ZSIsImR"
            "lc2NyaXB0aW9uIjoiVXBkYXRlL0VkaXQgYSB3YXlwb2ludCJ9LHsicGVybWlzc2lvbl9u"
            "YW1lIjoid2F5cG9pbnQ6ZGVsZXRlIiwiZGVzY3JpcHRpb24iOiJEZWxldGUgYSB3YXlwb"
            "2ludCJ9LHsicGVybWlzc2lvbl9uYW1lIjoibWlzc2lvbjpjcmVhdGUiLCJkZXNjcmlwdG"
            "lvbiI6IkNyZWF0ZSBhIG1pc3Npb24ifSx7InBlcm1pc3Npb25fbmFtZSI6Im1pc3Npb24"
            "6cmVhZCIsImRlc2NyaXB0aW9uIjoiR2V0IGEgbWlzc2lvbiJ9LHsicGVybWlzc2lvbl9u"
            "YW1lIjoibWlzc2lvbjp1cGRhdGUiLCJkZXNjcmlwdGlvbiI6IlVwZGF0ZS9FZGl0IGEgb"
            "Wlzc2lvbiJ9LHsicGVybWlzc2lvbl9uYW1lIjoibWlzc2lvbjpkZWxldGUiLCJkZXNjc"
            "mlwdGlvbiI6IkRlbGV0ZSBhIG1pc3Npb24ifSx7InBlcm1pc3Npb25fbmFtZSI6InNjaG"
            "VkdWxlOmNyZWF0ZSIsImRlc2NyaXB0aW9uIjoiQ3JlYXRlIGEgc2NoZWR1bGUifSx7InB"
            "lcm1pc3Npb25fbmFtZSI6InNjaGVkdWxlOnJlYWQiLCJkZXNjcmlwdGlvbiI6IkdldCBh"
            "IHNjaGVkdWxlIn0seyJwZXJtaXNzaW9uX25hbWUiOiJzY2hlZHVsZTp1cGRhdGUiLCJkZ"
            "XNjcmlwdGlvbiI6IlVwZGF0ZS9FZGl0IGEgc2NoZWR1bGUifSx7InBlcm1pc3Npb25fbm"
            "FtZSI6InNjaGVkdWxlOmRlbGV0ZSIsImRlc2NyaXB0aW9uIjoiRGVsZXRlIGEgc2NoZWR"
            "1bGUifSx7InBlcm1pc3Npb25fbmFtZSI6InJvYm90QWN0aW9uOnVzZSIsImRlc2NyaXB0"
            "aW9uIjoiVXNlIHRoZSByb2JvdCBhY3Rpb24gYnV0dG9uIn1dLCJkZWZhdWx0X3BhZ2UiO"
            "iJyb2JvdG9wcyIsInByb2ZpbGVfbmFtZSI6IkpvaG4gRG9lIiwiY29tcGFueV9pZCI6Ij"
            "E3YjBhYzUzLTc2ZmEtNDdmZC1hNmJmLWQyYWNlZjRmODdhYiIsIm9yZ2FuaXphdGlvbl9"
            "pZCI6ImVmNDkzYzU1LTMxNTQtNDQ3Ny05YzFmLWNjZDZkY2JhMmFkYiIsImF1dGhvcml6"
            "ZWQiOnRydWV9fQ.YsG8iDEo86iWvRSw30A7zWKUEsS38W7_me7H7zBnMmQ"
        ),
        "refresh_token": fields.String(
            example="eyJ0eXAiOiJKV1QiLCJhbGciOi"
            "JIUzI1NiJ9.eyJpYXQiOjE2NjcxOTM5NzgsIm5iZiI6MTY2NzE5Mzk3OCwianRpIj"
            "oiNTFhMmUwMzUtMWU1Mi00NDNhLTg2ZTUtZDJiOGM1NmY0MGM0IiwiZXhwIjoxNjY"
            "5Nzg1OTc4LCJpZGVudGl0eSI6InVzZXJuYW1lIiwidHlwZSI6InJlZnJlc2giLCJ1"
            "c2VyX2NsYWltcyI6eyJvcmdhbml6YXRpb25faWQiOiIxMjEyMTIifX0."
            "PkqjiDlf4VioSgu6WSItQkm-UICu9cRkVBEGTy_SQ2c"
        ),
    },
)

user_google_login_bad_response_model = user_ns2.model(
    "user_logout_response_ok_model",
    {
        "message": fields.String(
            example="An unexpected \
        error occured with Google Auth"
        )
    },
)

# User logout response models
user_logout_response_ok_model = user_ns2.model(
    "user_logout_response_ok_model",
    {"message": fields.String(example="User logged out")},
)
user_logout_bad_response_model = user_ns2.model(
    "user_logout_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# User registration response models
user_registration_response_ok_model = user_ns2.model(
    "user_registration_response_ok_model",
    {"teams_id": fields.String(example=str(uuid.uuid4()))},
)
user_registration_bad_response_model = user_ns2.model(
    "user_registration_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# User switch teams response models
user_switch_org_response_ok_model = user_ns2.model(
    "user_switch_org_response_ok_model",
    {"access_token": fields.String(example="access_token")},
)
user_switch_org_bad_response_model = user_ns2.model(
    "user_switch_org_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# User check mail response models
user_check_email_response_ok_model = user_ns2.model(
    "user_check_email_response_ok_model", user_row_dict
)

# User check teams info response models
user_check_teams_info_response_ok_model = user_ns2.model(
    "user_check_teams_info_response_ok_model",
    {"teams_name": fields.String(example="Bad request. Invalid input")},
)

user_check_email_bad_response_model = user_ns2.model(
    "user_check_email_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

user_fetch_response_row = user_row_dict.copy()
user_fetch_response_row.update(
    {"roles": fields.List(fields.String(example="role-details"))}
)

# User fetch response models
user_fetch_response_ok_model = user_ns2.model(
    "user_fetch_response_ok_model", user_fetch_response_row
)
user_fetch_bad_response_model = user_ns2.model(
    "user_fetch_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# User create response models
user_create_response_ok_model = user_ns2.model(
    "user_create_response_ok_model",
    {"user_id": fields.String(example=str(uuid.uuid4()))},
)
user_create_bad_response_model = user_ns2.model(
    "user_create_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# User update response models
user_update_row_dict = user_row_dict.copy()
user_update_row_dict.pop("password")
user_update_response_ok_model = user_ns2.model(
    "user_update_response_ok_model", user_row_dict
)
user_update_bad_response_model = user_ns2.model(
    "user_update_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# User search response models
user_search_row_dict = user_row_dict.copy()
user_search_row_dict.pop("password")
user_search_row_dict.pop("created_at")
user_search_row_dict.update(
    {
        "added_at": fields.String(example="10/31/2022, 06:16:40"),
    }
)

users_list_obj = user_search_row_dict.copy()
users_list_obj.update(
    {
        "is_email_verified": fields.Boolean(example=True),
        "roles": fields.List(fields.String(example="role-details")),
    }
)
users_list = {
    "user_list": fields.List(
        fields.Nested(user_ns2.model("users_list_obj", users_list_obj))
    )
}
user_search_response_ok_model = user_ns2.model(
    "user_search_response_ok_model", users_list
)
user_search_bad_response_model = user_ns2.model(
    "user_search_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# MFA activate response models
mfa_activate_response_ok_model = user_ns2.model(
    "mfa_activate_response_ok_model",
    {
        "message": fields.String(example="MFA has been activated"),
        "mfa_enabled": fields.Boolean(example=True),
    },
)
mfa_activate_bad_response_model = user_ns2.model(
    "mfa_activate_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# MFA deactivate response models
mfa_deactivate_response_ok_model = user_ns2.model(
    "mfa_deactivate_response_ok_model",
    {
        "message": fields.String(example="MFA has been deactivated"),
        "mfa_enabled": fields.Boolean(example=True),
    },
)
mfa_deactivate_bad_response_model = user_ns2.model(
    "mfa_deactivate_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# MFA fetch token response models
mfa_fetch_token_response_ok_model = user_ns2.model(
    "mfa_fetch_token_response_ok_model",
    {"message": fields.String(example="Downloadable file")},
)
mfa_fetch_token_bad_response_model = user_ns2.model(
    "mfa_fetch_token_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# Fetch user notification status response models
fetch_notification_status_response_ok_model = user_ns2.model(
    "fetch_notification_status_response_ok_model",
    {
        "user_id": fields.String(str(uuid.uuid4())),
        "notifications_status": fields.Boolean(example=True),
        "mfa_enabled": fields.Boolean(example=True),
    },
)
fetch_notification_status_bad_response_model = user_ns2.model(
    "fetch_notification_status_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# Update notification status of user
update_notification_status_response_ok_model = user_ns2.model(
    "update_notification_status_response_ok_model",
    {
        "preference_id": fields.String(example=str(uuid.uuid4())),
        "user_id": fields.String(example=str(uuid.uuid4())),
        "notifications_enabled": fields.Boolean(example=True),
        "added_at": fields.DateTime(example="2022-10-10T10:00:00.123456"),
    },
)
update_notification_status_bad_response_model = user_ns2.model(
    "update_notification_status_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# User teams fetch response models
user_org_dict = {
    "teams_id": fields.String(example=str(uuid.uuid4())),
    "teams_name": fields.String(example="Cognicept Systems"),
    "owner": fields.String(example=str(uuid.uuid4())),
    "created_at": fields.String(example="2022-08-17 11:38:07.823404"),
    "updated_at": fields.String(example="2022-08-17 11:38:07.823404"),
    "is_disabled": fields.Boolean(example=True),
    "is_deleted": fields.Boolean(example=True),
}
orgs_list = {
    "org_list": fields.List(
        fields.Nested(user_ns2.model("user_org_dict", user_org_dict))
    )
}

user_fetch_org_response_ok_model = user_ns2.model(
    "user_fetch_org_response_ok_model", orgs_list
)
user_fetch_org_bad_response_model = user_ns2.model(
    "user_fetch_org_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# User delete response models
user_delete_response_ok_model = user_ns2.model(
    "user_delete_response_ok_model",
    {"user_id": fields.String(example=str(uuid.uuid4()))},
)
user_delete_bad_response_model = user_ns2.model(
    "user_delete_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# User reset password response models
user_pwd_reset_response_ok_model = user_ns2.model(
    "user_pwd_reset_response_ok_model",
    {
        "message": fields.String(
            example="Password has been reset! Redirecting to Login page"
        )
    },
)
user_pwd_reset_bad_response_model = user_ns2.model(
    "user_pwd_reset_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# User forgot password response models
user_forgot_pwd_response_ok_model = user_ns2.model(
    "user_forgot_pwd_response_ok_model",
    {
        "message": fields.String(
            example=' "You will receive reset password email " '
            "if the user exists in our database. Redirecting to Login page"
        )
    },
)
user_forgot_pwd_bad_response_model = user_ns2.model(
    "user_forgot_pwd_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# Validate password token response models
user_validate_pwd_token_response_ok_model = user_ns2.model(
    "user_validate_pwd_token_response_ok_model",
    {"message": fields.String(example="Token is valid")},
)
user_validate_pwd_token_bad_response_model = user_ns2.model(
    "user_validate_pwd_token_bad_response_model",
    {"message": fields.String(example="Bad request. Invalid input")},
)

# user dashboard response models
user_dashboard_response_ok_model = user_ns2.model(
    "user_dashboard_response_ok_model",
    {"dashboard_url": fields.String(example="https://domain/d/Sh4lSPFVk/test")},
)
user_dashboard_bad_response_model = user_ns2.model(
    "user_dashboard_bad_response_model", {"message": fields.String(example="user_id")}
)


class UserLogin(Resource):
    """class for /user/login functionalities"""

    @user_ns2.expect(user_password_model)
    @user_ns2.doc(security=None)
    @user_ns2.response(200, "OK", user_login_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_login_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def post(self):
        """Used for logging in user"""
        request_data = user_ns2.payload
        input_username = request_data["username"]
        input_password = request_data["password"]
        input_device_id = request_data.get("device_id", "")

        user_details = user_services.check_user_exists(username=input_username)
        if not user_details:
            return {
                "message": "Username and password combination not valid".format(
                    input_username
                )
            }, 200
        if not user_services.validate_password(input_username, input_password):
            return {"message": "Username and password combination not valid"}, 200
        user_services.update_user_last_active_at(user_details.user_id)
        """
        Handle orphan user
        @Author: Thinh Le
        """
        default_teams = user_services.get_default_org(user_details.user_id)
        user_teams = teams_services.get_user_org_list(user_details.user_id)
        if not default_teams:
            org_list = user_teams.get("org_list", [])
            if len(org_list) > 0:
                set_user_default_teams(user_details.user_id, org_list[0]["teams_id"])
            else:
                return {'message': 'Vui lòng liên hệ admin để thêm bạn vào Teams'}, 400
                # Try to create user default org
                # if user_details.first_name and user_details.last_name:
                #     profile_name = (
                #         user_details.first_name + " " + user_details.last_name
                #     )
                # else:
                #     profile_name = "User"
                # (
                #     org_id,
                #     err_data,
                #     err_code,
                # ) = user_services.create_default_user_teams(
                #     current_app,
                #     user_details,
                #     profile_name,
                # )
                # if not org_id:
                #     return err_data, err_code

        return user_services.get_user_auth_tokens(user_details, input_device_id), 200


class UserRefresh(Resource):
    """class for /user/refresh endpoint to get the new access token using refresh token
    Returns:
        access_token:string
    """

    @jwt_refresh_token_required
    @user_ns2.response(200, "OK", user_login_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_login_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def post(self):
        try:
            username = get_jwt_identity()
            refresh_jti = get_raw_jwt()["jti"]
            if user_services.validate_auth_token({"jti": refresh_jti}):
                return {"message": "Not authorized"}, 401
            user_details = user_services.check_user_exists(username=username)
            if not user_details:
                return {
                    "message": "Username and password combination not valid".format(
                        username
                    )
                }, 200
            user_details = user_services.row_to_dict(user_details)
            teams_id = get_jwt_claims()["teams_id"]
            teams_code = get_jwt_claims()["teams_code"]
            db.session.execute("SET search_path TO public, 'cs_" + str(teams_id) + "'")
            permissions = user_services.get_user_permissions(username)
            roles = user_services.get_user_roles(username, teams_id)
            is_mfa_enabled = user_services.get_mfa_status(user_details.get("user_id"))
            if (
                user_details.get("first_name") is not None
                and user_details.get("last_name") is not None
            ):
                profile_name = str(
                    user_details.get("first_name", "")
                    + " "
                    + user_details.get("last_name", "")
                )
            else:
                profile_name = user_details.get("username")
            user_payload = {
                "user": username,
                "user_id": user_details.get("user_id"),
                "role": roles,
                "permissions": permissions,
                "default_page": user_details.get("default_page", ""),
                "profile_name": profile_name,
                "teams_id": str(teams_id),
                "teams_code": str(teams_code).lower(),
                "authorized": True,
                "refresh_jti": refresh_jti,
            }
            user_services.update_user_last_active_at(user_details.get("user_id"))
            access_token = create_access_token({**user_payload, "type": "access"})
            return jsonify(access_token=access_token)
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


class UserResetPassword(Resource):
    """class for /user/password functionalities"""

    @custom_jwt_required()
    @user_ns2.expect(user_reset_password_model)
    @user_ns2.response(200, "OK", user_pwd_reset_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_pwd_reset_bad_response_model)
    def put(self):
        """Used to reset password for a user"""
        try:
            request_data = user_ns2.payload
            old_password = request_data["old_password"]
            new_password = request_data["new_password"]
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad Request. Invalid input"}, 400
        try:
            claims = get_jwt_claims()
            if not user_services.validate_password(claims["user"], old_password):
                return {
                    "message": "The old password you have entered is incorrect"
                }, 200
            if new_password != "":
                user_services.reset_password(claims["user"], new_password)
            else:
                return {"message": "Password cannot be empty"}, 200
            return {
                "message": "Password has been reset! Redirecting to Login page"
            }, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


class UserLogout(Resource):
    """Blacklisting token on logout"""

    @custom_jwt_required()
    @user_ns2.response(200, "OK", user_logout_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_logout_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def delete(self):
        """Used to blacklist user token during logout"""
        try:
            claims = get_jwt_claims()
            user_services.blacklist_token(get_raw_jwt()["jti"])
            if claims.get("refresh_jti"):
                user_services.blacklist_token(claims["refresh_jti"])
            return {"message": "User logged out"}, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


class UserGet(Resource):
    """class for /user/get functionalities"""

    @custom_jwt_required()
    @user_ns2.response(200, "OK", user_fetch_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_fetch_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(401, "Token expired", token_expired_response_model)
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def get(self, username):
        """Used to retrive a user from username"""
        user_details = user_services.get_user_details(username=username)
        claims = get_jwt_claims()
        teams_id = claims["teams_id"]
        if not user_details:
            return {"message": "User {} does not exist".format(username)}, 200
        user_details = user_services.row_to_dict(user_details)
        del user_details["password"]
        roles = user_services.get_user_roles(username, teams_id)
        user_details["roles"] = roles
        return user_details, 200


class UserOperations(Resource):
    """class for /user functionalities"""

    @custom_jwt_required()
    @user_ns2.expect(user_create_model)
    @user_ns2.response(200, "OK", user_create_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_create_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def post(self):
        """Used to create a user"""
        request_data = user_ns2.payload
        username = request_data["username"]
        password = request_data["password"]
        first_name = request_data.get("first_name", None)
        last_name = request_data.get("last_name", None)
        role_id = request_data.get("role_id", None)

        if user_services.check_user_exists(username=username):
            return {"message": "User {} already exists.".format(username)}, 400
        if password == "":
            return {"message": "Password cannot be empty"}, 401

        new_user = user_services.create_user(username, password, first_name, last_name)
        user_claims = get_jwt_claims()
        teams_id = user_claims["teams_id"]
        user_services.update_user_email_verification(new_user.user_id)
        db.session.execute("SET search_path TO public, 'cs_" + str(teams_id) + "'")
        user_services.create_user_role_mapping(new_user.user_id, role_id, teams_id)
        user_services.create_user_teams_mapping(new_user.user_id, teams_id)
        return {"user_id": str(new_user.user_id)}, 200

    @custom_jwt_required()
    @user_ns2.expect(user_update_model)
    @user_ns2.response(200, "OK", user_update_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_update_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def put(self):
        """Used to update a user"""
        try:
            request_data = user_ns2.payload
            username = request_data["username"]
            first_name = request_data.get("first_name")
            last_name = request_data.get("last_name")
            role_id = request_data.get("role_id")
            password = request_data.get("password")
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400

        claims = get_jwt_claims()
        teams_id = claims["teams_id"]
        user = user_services.check_user_exists(username=username)
        if not user:
            return {"message": "User {} does not exist".format(username)}, 400
        is_admin = True
        if not any(
            role["role_name"] == RoleName.Administrator.value for role in claims["role"]
        ):
            is_admin = False
            if username != get_jwt_identity():
                return {"message": "User not authorized for this operation"}, 403
        if is_admin:
            user_details = user_services.update_user(
                username, first_name, last_name, role_id, password, teams_id
            )
        else:
            user_details = user_services.update_user(
                username, first_name, last_name, "", password, teams_id
            )
        return user_details, 200

    @custom_jwt_required()
    @user_ns2.expect(user_id_parser)
    @user_ns2.response(200, "OK", user_delete_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_delete_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def delete(self):
        """Used to delete a user"""
        try:
            user_id = user_id_parser.parse_args()["user_id"]
            current_username = get_jwt_identity()
            claims = get_jwt_claims()
            teams_id = claims["teams_id"]
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad Request. Invalid input"}, 400
        try:
            roles = claims["role"]
            is_admin = user_services.check_is_administrator_user(roles)
            if not is_admin:
                return {"message": "Not Authorized"}, 403
            # Check if user exists
            if user_services.check_user_exists(user_id=user_id):
                # Delete user org mapping
                user_services.delete_user_teams_mapping(user_id, teams_id)
                user_services.delete_user_preference(user_id)
                user_services.delete_user_role_mapping(user_id, teams_id)
                # Disable user
                if user_services.disable_user(user_id):
                    return {"user_id": str(user_id)}, 200
                return {"msg": "can not delete this user"}, 400
            return {"msg": "user does not exist"}, 400
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400

    @custom_jwt_required()
    @user_ns2.response(200, "OK", user_search_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_search_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def get(self):
        """Used to retrieve list of users"""
        claims = get_jwt_claims()
        teams_id = claims["teams_id"]
        is_administrator = user_services.check_is_administrator_user(claims.get("role"))
        result = []
        if is_administrator:
            users = user_services.get_user_list()
            for each_user in users:
                roles = user_services.get_user_roles(each_user["username"], teams_id)
                is_administrator = user_services.check_is_administrator_user(roles)
                each_user["roles"] = (
                    UserRoleEnums.Admin.value
                    if is_administrator
                    else UserRoleEnums.User.value
                )
                result.append(each_user)
            return {"user_list": result}, 200
        # client does not have permissions to get user list
        return {"user_list": []}, 200


class UserSwitchTeams(Resource):
    """class for /user/switch_org functionalities"""

    @user_ns2.expect(switch_org_model)
    @custom_jwt_required()
    @user_ns2.response(200, "OK", user_switch_org_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_switch_org_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def post(self):
        """Used to switch teams of a user"""
        try:
            request_data = user_ns2.payload
            teams_id = request_data["teams_id"]

            claims = get_jwt_claims()
            username = get_jwt_identity()
            device_id = claims["device_id"]
            user_id = claims["user_id"]
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400

        teams = teams_services.get_teams(teams_id)
        if not teams:
            return {"message": "Team not found"}, 400

        if teams_id == claims["teams_id"]:
            # Return the same JWT from request header
            access_token = request.headers.get("Authorization").split(" ")[1]
            token = {"access_token": access_token}
            return token, 200

        try:
            # Added super admin functionality here.
            #  Using this user, we can access any teams.
            #  This user's credentials have to be SUPER SECRET.
            super_admin = UserTypeEnums.SuperAdmin.value
            if super_admin == user_id:
                user_payload = {
                    "user": username,
                    "user_id": user_id,
                    "role": claims.get("role"),
                    "device_id": device_id,
                    "permissions": claims.get("permissions"),
                    "default_page": claims.get("default_page", ""),
                    "profile_name": claims.get("profile_name", ""),
                    "teams_id": str(teams_id),
                    "teams_code": claims.get("teams_code", "").lower(),
                    "authorized": claims.get("authorized"),
                }
                refresh_token = create_refresh_token(
                    {**user_payload, "type": "refresh"}
                )
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
                return token, 200
            elif user_services.check_user_teams_mapping(user_id, teams_id):
                migration_services.set_search_path(teams_id)
                permissions = user_services.get_user_permissions(username)
                roles = user_services.get_user_roles(username, teams_id)
                user_payload = {
                    "user": username,
                    "user_id": user_id,
                    "role": roles,
                    "device_id": device_id,
                    "permissions": permissions,
                    "default_page": claims.get("default_page", ""),
                    "profile_name": claims.get("profile_name", ""),
                    "teams_id": str(teams_id),
                    "teams_code": claims.get("teams_code", "").lower(),
                    "authorized": claims.get("authorized"),
                }
                refresh_token = create_refresh_token(
                    {**user_payload, "type": "refresh"}
                )
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
                if blacklist:
                    user_services.blacklist_token(get_raw_jwt()["jti"])
                    if claims["refresh_jti"]:
                        user_services.blacklist_token(claims["refresh_jti"])
                return token, 200
            else:
                return {"message": "User does not belong to teams"}, 400
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 500


class UserTeamsOperations(Resource):
    """class for /user/teams functionalities"""

    @custom_jwt_required()
    @user_ns2.response(200, "OK", user_fetch_org_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_fetch_org_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def get(self):
        """Used to retrieve list of teamss of a user"""
        try:
            claims = get_jwt_claims()
            user_id = claims["user_id"]
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message", "No user_id in JWT"}, 400
        try:
            org_list = teams_services.get_user_org_list(user_id)
            return org_list, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 400


class UserCheck(Resource):
    """class for /user/info functionalities"""

    @custom_jwt_required()
    @user_ns2.response(200, "OK", user_check_email_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_check_email_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def get(self):
        """Used to check whether user exists"""
        username = get_jwt_identity()
        user_claims = get_jwt_claims()
        teams_id = user_claims["teams_id"]
        user = user_services.check_user_info(teams_id=teams_id, username=username)
        if user is None:
            return {"message": "user does not exist"}, 200
        user_data = user.repr_name()
        user_role_mapping = user_services.get_user_roles(username, teams_id)

        user_data["is_super_admin"] = (
            True if user_data["user_id"] == UserTypeEnums.SuperAdmin.value else False
        )
        if user_data["is_super_admin"]:
            user_data["is_admin"] = True
        else:
            user_data["is_admin"] = (
                True
                if [
                    role
                    for role in user_role_mapping
                    if role["role_id"] == UserRoleEnums.AdminId.value
                ]
                else False
            )

        return user_data, 200


class UserTeamInfoOperations(Resource):
    @custom_jwt_required()
    @user_ns2.response(200, "OK", user_check_teams_info_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_check_email_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def get(self):
        """Used to check whether user exists"""
        claims = get_jwt_claims()
        teams_id = claims["teams_id"]
        teams = teams_services.get_teams(teams_id=teams_id)

        if teams is None:
            return {"message": "user does not exist"}, 200

        return teams.repr_name(), 200


class UserRegistration(Resource):
    """class for /user/registration functionalities"""

    @user_ns2.expect(user_register_model)
    @user_ns2.response(200, "OK", user_registration_response_ok_model)
    @user_ns2.response(400, "Bad Request", user_registration_bad_response_model)
    @user_ns2.response(
        401,
        "Authorization information is missing or invalid.",
        unauthorized_response_model,
    )
    @user_ns2.response(500, "Internal Server Error", internal_server_error_model)
    def post(self):
        """Used to register a user"""
        try:
            request_data = user_ns2.payload
            username = request_data["username"].strip()
            password = request_data["password"].strip()
            first_name = (
                request_data["first_name"].strip()
                if "first_name" in request_data
                else None
            )
            last_name = (
                request_data["last_name"].strip()
                if "last_name" in request_data
                else None
            )
            org_name = request_data["teams_name"].strip()
            profile_name = (
                "User" if first_name and last_name else f"{first_name} {last_name}"
            )
        except Exception as e:
            _logger.debug(f"Request validation failed: {e}")
            return {"message": "Bad request. Invalid input"}, 400
        valid_password = user_services.check_user_password_criteria(password)
        valid_username = user_services.is_valid_username(username)
        if not valid_password:
            return {"message": "Mật khẩu quá ngắn"}, 400
        if not valid_username:
            return {"message": "Username không phù hợp"}, 400
        try:
            # If username exists, abort.
            if user_services.check_user_exists(username=username):
                return {"message": "Tài khoản {} đã tồn tại".format(username)}, 400

            # Create user in user table
            new_user = user_services.create_user(
                username, password, first_name, last_name
            )

            # Create user's default organization
            # teams_id, err_data, err_code = user_services.create_default_user_teams(
            #     current_app,
            #     new_user,
            #     profile_name,
            #     org_name,
            # )
            # if not teams_id:
            #     teams_services.rollback_teams_creation(teams_id, new_user.user_id)
            #     return err_data, err_code
            return {"message": "Tạo thành công, vui lòng liên hệ admin để bắt đầu sử dụng tools"}, 200
        except Exception as err:
            _logger.exception(err)
            return {"message": str(err)}, 500


user_ns2.add_resource(UserLogin, "/login")
user_ns2.add_resource(UserRefresh, "/refresh")
user_ns2.add_resource(UserLogout, "/logout")
user_ns2.add_resource(UserOperations, "")
user_ns2.add_resource(UserRegistration, "/registration")
user_ns2.add_resource(UserSwitchTeams, "/switch_team")
user_ns2.add_resource(UserTeamsOperations, "/teams")
user_ns2.add_resource(UserTeamInfoOperations, "/team_info")
user_ns2.add_resource(UserCheck, "/info")
